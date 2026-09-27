import {
  useCallback,
  useMemo,
} from "react";

import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
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

  const nodes = useMemo(() => {

    const columns = 4;

    const horizontalGap = 250;

    const verticalGap = 170;

    return caseData.entities.map(
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

          data: entity,
        };
      }
    );

  }, [caseData.entities]);

  /*
   * ==========================================================
   * EDGES
   * ==========================================================
   */

  const edges = useMemo(
    () =>
      caseData.relationships.map(
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

    [caseData.relationships]
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
          caseData.entities.find(
            (item) =>
              item.id === node.id
          );

        if (entity) {
          onEntitySelect(
            entity
          );
        }

      },
      [
        caseData.entities,
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

        <MiniMap />

      </ReactFlow>

    </div>
  );
}

export default NetworkGraph;