from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import GraphEdge, GraphNode
from app.schemas import GraphPayload

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphPayload)
def full_graph(
    paper_id: int | None = None,
    db: Session = Depends(get_db),
) -> GraphPayload:
    nodes_q = db.query(GraphNode)
    if paper_id is not None:
        nodes_q = nodes_q.filter(GraphNode.paper_id == paper_id)
    nodes = nodes_q.order_by(GraphNode.id).all()

    if paper_id is not None:
        node_ids = {n.id for n in nodes}
        edges = (
            db.query(GraphEdge)
            .filter(
                GraphEdge.source_node_id.in_(node_ids)
                | GraphEdge.target_node_id.in_(node_ids)
            )
            .all()
        )
    else:
        edges = db.query(GraphEdge).order_by(GraphEdge.id).all()

    return GraphPayload(nodes=nodes, edges=edges)
