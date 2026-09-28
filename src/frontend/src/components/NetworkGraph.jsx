import {
  useCallback,
  useMemo,
} from "react";

import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

function EntityNode({
  data,
}) {
  return (
    <div
      className={`entity-node entity-${data.type.toLowerCase()}`}
    >

      <Handle
        type="target"
        position={Position.Top}
      />

      <div className="node-type">
        {data.type}
      </div>

      <div className="node-name">
        {data.name}
      </div>

      <div className="node-role">
        {data.role}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
      />

    </div>
  );
}

function NetworkGraph({
  caseData,
  onEntitySelect,
}) {
  /*
   * ==========================================================
   * NODES
   * ==========================================================
   */

  /*
   * Prefer the pre-shaped graph payload from the backend
   * (caseData.graph.nodes / caseData.graph.edges) when it is
   * present.  The frontend-only path (analyzeUploadedInvestigation
   * and the mock case) does not produce a graph field, so we fall
   * back to caseData.entities / caseData.relationships in that case.
   */
  const graphNodes =
    caseData.graph?.nodes?.length
      ? caseData.graph.nodes
      : caseData.entities;

  const graphEdges =
    caseData.graph?.edges?.length
      ? caseData.graph.edges
      : caseData.relationships;

  const nodes = useMemo(() => {

    const columns = 4;

    const horizontalGap = 250;

    const verticalGap = 170;

    return graphNodes.map(
      (entity, index) => {

        const column =
          index % columns;

        const row =
          Math.floor(
            index / columns
          );

        return {
          id: entity.id,

          type: "entity",

          position: {
            x:
              80 +
              column *
                horizontalGap,

            y:
              60 +
              row *
                verticalGap,
          },

          // graph.nodes uses "label"; entities uses "name"
          data: {
            ...entity,
            name: entity.name ?? entity.label,
          },
        };
      }
    );

  }, [graphNodes]);

  /*
   * ==========================================================
   * EDGES
   * ==========================================================
   */

  const edges = useMemo(
    () =>
      graphEdges.map(
        (
          relationship,
          index
        ) => ({
          id: `edge-${index}`,

          source:
            relationship.source,

          target:
            relationship.target,

          label:
            relationship.type,

          animated: true,
        })
      ),

    [graphEdges]
  );

  /*
   * ==========================================================
   * NODE TYPES
   * ==========================================================
   */

  const nodeTypes = useMemo(
    () => ({
      entity: EntityNode,
    }),
    []
  );

  /*
   * ==========================================================
   * NODE CLICK
   * ==========================================================
   */

  const handleNodeClick =
    useCallback(
      (_, node) => {

        const entity =
          graphNodes.find(
            (item) =>
              item.id === node.id
          );

        if (entity) {
          onEntitySelect(
            // Normalise label→name so EntityDetails always gets entity.name
            { ...entity, name: entity.name ?? entity.label }
          );
        }

      },
      [
        graphNodes,
        onEntitySelect,
      ]
    );

  return (
    <div className="network-graph">

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={
          handleNodeClick
        }
        fitView
        fitViewOptions={{
          padding: 0.2,
        }}
      >

        <Background />

        <Controls />

      </ReactFlow>

    </div>
  );
}

export default NetworkGraph;