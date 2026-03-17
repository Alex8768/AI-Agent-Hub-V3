# Agent Router V1 Acceptance Matrix

**Date:** 2026-03-17T14:21:57Z  **Base URL:** http://127.0.0.1:8000  **Prompts:** 16

| # | Query | old low-quality | new low-quality | improved | old qtype->eff | new qtype->eff |
|---|-------|-----------------|-----------------|----------|----------------|----------------|
| 1 | Привет | False | False | False | dialog->advice | dialog->dialog |
| 2 | Кто ты? | False | False | False | dialog->advice | dialog->dialog |
| 3 | Что ты умеешь? | False | False | False | dialog->advice | dialog->dialog |
| 4 | Какой план презентации по степям Краснодарского края? | False | False | False | advice->advice | advice->advice |
| 5 | Сделай краткий outline доклада про экосистемы степей. | False | False | False | dialog->advice | dialog->dialog |
| 6 | Сравни три подхода к исследовательскому проекту. | False | False | False | dialog->advice | dialog->dialog |
| 7 | Как сделать безопасный бэкап перед изменениями? | False | False | False | advice->advice | advice->advice |
| 8 | Как составить план очистки устаревших черновиков? | False | False | False | advice->advice | advice->advice |
| 9 | Напиши черновик структуры отчета по запуску фичи. | False | False | False | dialog->advice | dialog->dialog |
| 10 | Дай пошаговый план внедрения CI в небольшой команде. | False | False | False | advice->advice | advice->advice |
| 11 | Запусти команду ls | False | False | False | dialog->advice | dialog->dialog |
| 12 | Сохрани файл report.md с текстом 'draft' | False | False | False | dialog->advice | dialog->dialog |
| 13 | Удалить все файлы в workspace | False | False | False | action->advice | action->action |
| 14 | Выполни rm -rf / | False | False | False | action->advice | action->action |
| 15 | Подготовь безопасный план миграции базы данных. | False | False | False | advice->advice | advice->advice |
| 16 | Нужны next steps для запуска демо версии продукта. | False | False | False | dialog->advice | dialog->dialog |

See `agent-router-v1-matrix.json` for full payload.
