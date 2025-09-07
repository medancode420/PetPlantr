.PHONY: test-sprint-c
test-sprint-c:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q -m sprint_c -c pytest.ini

.PHONY: test-sprint-c-sample
test-sprint-c-sample:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_ops_sync_subscriber.py tests/test_ops_sync_subscriber_edges.py -c pytest.ini

.PHONY: qa-report
qa-report:
	@echo "🎯 Running QA Report..."
	@python3 -c "from src.qa_system import BreedQASystem; qa_system = BreedQASystem(); report = qa_system.export_qa_report(); print('🎯 QA System Report'); print('=' * 50); print(f'Precision: {report[\"qa_metrics\"][\"precision\"]:.1%}'); print(f'Status: {report[\"qa_status\"]}'); print(f'Reviewed Samples: {report[\"qa_metrics\"][\"total_reviewed\"]}'); exit(0 if report['qa_status'] == 'PASS' else 1)"