"""Evalúa negativos externos congelados sin reajustar el filtro de alcance."""
from pathlib import Path
import argparse, csv, hashlib, json, sys, time

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT.parent.parent / 'work' / 'pydeps'
if DEPS.exists():
    sys.path.insert(0, str(DEPS))
sys.path.insert(0, str(ROOT))

from palimpsesto.imaging import load_image
from palimpsesto.models import ModelService
from palimpsesto.validation import assess_input


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def count(records, predicate):
    return sum(bool(predicate(record)) for record in records)


def summarize(records):
    result = {}
    for label in ['total', *sorted({record['label'] for record in records})]:
        subset = records if label == 'total' else [record for record in records if record['label'] == label]
        result[label] = {
            'n': len(subset),
            'scope_flagged': count(subset, lambda r: r['scope_flagged']),
            'scope_missed': count(subset, lambda r: not r['scope_flagged']),
            'scope_recall': round(count(subset, lambda r: r['scope_flagged']) / len(subset), 4),
            'any_exception': count(subset, lambda r: r['exception_triggered']),
        }
    return result


def interpretation(summary):
    total = summary['total']['scope_flagged']
    per_label = [value['scope_flagged'] for key, value in summary.items() if key != 'total']
    if total >= 27 and min(per_label) >= 8:
        return {
            'level': 'documentar_sin_recalibrar',
            'reason': 'Se alertó al menos 90 % del total y al menos 8/10 de cada etiqueta.',
            'next_step': 'Conservar el filtro v0.4.0, documentar fallos concretos y no ajustar con este conjunto.'
        }
    if total >= 24 and min(per_label) >= 6:
        return {
            'level': 'ampliar_desarrollo',
            'reason': 'El resultado queda entre 80 % y 89,9 %, o alguna etiqueta queda entre 6/10 y 7/10.',
            'next_step': 'No recalibrar con estas 30. Crear negativos adicionales para desarrollo, formular un cambio y reservar otra prueba final independiente.'
        }
    return {
        'level': 'revision_prioritaria',
        'reason': 'Se alertó menos de 80 % del total o alguna etiqueta quedó por debajo de 6/10.',
        'next_step': 'Mantener la confirmación humana obligatoria. Construir desarrollo negativo independiente, revisar el método y evaluar de nuevo en otro conjunto ciego.'
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True, type=Path, help='Carpeta negativos_alcance_v1')
    parser.add_argument('--out', default=ROOT / 'results' / 'scope' / 'external_negatives_v1.json', type=Path)
    args = parser.parse_args()
    data = args.data.resolve()
    manifest = data / 'manifest.csv'
    rows = list(csv.DictReader(manifest.open(encoding='utf-8-sig')))
    if len(rows) != 30 or any(row['expected_scope'] != 'fuera_de_alcance' for row in rows):
        raise ValueError('Se esperaba un manifiesto congelado de 30 negativos.')
    if any(row['model_used_for_selection'].lower() != 'false' for row in rows):
        raise ValueError('La selección no es independiente del modelo.')

    model = ModelService(ROOT / 'models')
    if model.classifier is None or model.scope_bank is None:
        raise RuntimeError('El clasificador o su banco de alcance no están disponibles.')

    records = []
    started = time.perf_counter()
    for row in rows:
        path = data / row['final_path']
        if sha256(path) != row['sha256']:
            raise ValueError(f"El hash no coincide: {row['image_id']}")
        rgb, _ = load_image(path.read_bytes())
        prediction = model.classify(rgb)
        scope = prediction.get('scope') or {}
        assessment = assess_input(rgb, prediction)
        scores = prediction.get('scores') or {}
        records.append({
            'image_id': row['image_id'],
            'label': row['label'],
            'content': row['content'],
            'source_name': row['source_name'],
            'sha256': row['sha256'],
            'scope_flagged': bool(scope.get('flagged')),
            'exception_triggered': bool(assessment['requires_confirmation']),
            'reasons': assessment['reasons'],
            'similarity': round(float(scope['similarity']), 6),
            'threshold': round(float(scope['threshold']), 6),
            'suggested_class': prediction.get('class'),
            'top_score': round(max(scores.values()), 6) if scores else None,
        })

    summary = summarize(records)
    report = {
        'protocol': {
            'selection': '30 fotografías propias seleccionadas visualmente antes de consultar el modelo; una toma por identidad física o escena.',
            'expected': 'Todas fuera de alcance.',
            'primary_metric': 'Proporción marcada scope_flagged; any_exception se informa aparte porque también puede incluir detección de rostro.',
            'decision_rule_predeclared': {
                'documentar_sin_recalibrar': '>=27/30 y >=8/10 en cada etiqueta',
                'ampliar_desarrollo': '>=24/30 y >=6/10 en cada etiqueta, sin cumplir la regla anterior',
                'revision_prioritaria': '<24/30 o alguna etiqueta <6/10',
            },
            'no_tuning': 'No se modificaron pesos, banco, umbral ni selección después de observar las salidas.'
        },
        'dataset': {
            'manifest_sha256': sha256(manifest),
            'n': len(rows),
            'labels': sorted({row['label'] for row in rows}),
        },
        'model': {
            'classifier_sha256': sha256(ROOT / 'models' / 'classifier.pt'),
            'scope_reference_sha256': sha256(ROOT / 'models' / 'scope_reference.npz'),
            'scope_threshold': records[0]['threshold'],
        },
        'summary': summary,
        'interpretation': interpretation(summary),
        'elapsed_seconds': round(time.perf_counter() - started, 3),
        'cases': records,
        'limitations': 'Prueba externa de conveniencia de 30 negativos propios. No demuestra detección universal de objetos desconocidos ni mide falsos positivos sobre piezas válidas.'
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    csv_path = args.out.with_suffix('.csv')
    with csv_path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=[key for key in records[0] if key != 'reasons'])
        writer.writeheader()
        writer.writerows({key: value for key, value in record.items() if key != 'reasons'} for record in records)
    print(json.dumps({'summary': summary, 'interpretation': report['interpretation'], 'out': str(args.out)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
