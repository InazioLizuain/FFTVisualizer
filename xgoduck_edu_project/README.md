# XGoDuck Educational Replica Starter

Plantilla base para arrancar una réplica educativa de hardware + software inspirada en:
- https://github.com/luwudynamics/xgoduck_runtime_arduino
- https://github.com/luwudynamics/xgoduck_hardware

## Objetivo
Crear un entorno de trabajo reproducible para:
1. Validar viabilidad técnica/legal.
2. Replicar HW/SW por capas.
3. Documentar aprendizaje y decisiones.

## Estructura
- `hardware/`: diseño, ensamblaje y verificación física
- `firmware/`: firmware de bajo nivel y control
- `runtime/`: lógica de ejecución/alto nivel
- `training/`: datasets, pipeline y evaluación
- `bom/`: lista de materiales y equivalencias
- `calibration/`: procedimientos reproducibles de calibración
- `tests/`: plan y resultados de pruebas
- `docs/`: guía del proyecto, riesgos y roadmap

## Primeros pasos
1. Completar `docs/01_validation.md`.
2. Fijar referencias en `docs/02_reference_freeze.md`.
3. Completar matriz de disponibilidad en `bom/bom_status_matrix.csv`.
4. Ejecutar bring-up con `hardware/ASSEMBLY_CHECKLIST.md`.
5. Registrar pruebas en `tests/MODULE_TEST_PLAN.md`.

## Nota
Este material es educativo. Verifica siempre licencias, atribución y restricciones de uso.
