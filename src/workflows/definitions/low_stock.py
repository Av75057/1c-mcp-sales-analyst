from src.workflows.models import Workflow, WorkflowStep

LOW_STOCK_WORKFLOW = Workflow(
    name="low_stock_handling",
    description="Автоматическая обработка низкого остатка",
    steps=[
        WorkflowStep(name="notify_manager", event_type="stock_low", handler="notify_stock_manager", next_step="create_purchase_order"),
        WorkflowStep(name="create_purchase_order", event_type="stock_low", handler="create_purchase_order", condition="data.get('quantity',0) < data.get('min_qty',10) * 0.5", next_step="notify_purchase_created"),
        WorkflowStep(name="notify_purchase_created", event_type="stock_low", handler="notify_purchase_created"),
    ],
)
