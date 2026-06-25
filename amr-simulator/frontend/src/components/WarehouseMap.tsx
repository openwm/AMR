import type { AMR, WarehouseLayout } from "../types";

const CELL = 64;
const HALF = CELL / 2;
const PAD  = 48;

const ZONE_COLORS: Record<string, string> = {
  A: "#dbeafe",
  B: "#dcfce7",
  C: "#fef3c7",
  D: "#fce7f3",
};

const STATUS_COLORS: Record<string, string> = {
  idle:        "#94a3b8",
  traveling:   "#3b82f6",
  at_location: "#22c55e",
};

interface Props {
  layout: WarehouseLayout;
  amrs: AMR[];
}

function cellX(x: number) { return PAD + x * CELL; }
function cellY(y: number) { return PAD + y * CELL; }

export function WarehouseMap({ layout, amrs }: Props) {
  const { grid_width, grid_height, zone_labels, locations, stations } = layout;

  const W = (grid_width + 1) * CELL + PAD * 2;
  const H = (grid_height + 1) * CELL + PAD * 2;

  const stationCodes = new Set(Object.keys(stations));
  const dockCodes    = new Set(["DOCK-IN", "DOCK-OUT"]);

  const storageEntries = Object.entries(locations).filter(
    ([code]) => !stationCodes.has(code) && !dockCodes.has(code)
  );

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      style={{ background: "#f8fafc", display: "block" }}
    >
      {/* Zone color bands (skip row 0 dock, skip station row at bottom) */}
      {zone_labels.map((z) => (
        <rect
          key={z.zone}
          x={cellX(z.x_start)}
          y={cellY(1)}
          width={(z.x_end - z.x_start + 1) * CELL}
          height={(grid_height - 2) * CELL}
          fill={ZONE_COLORS[z.zone] ?? "#e2e8f0"}
          opacity={0.35}
        />
      ))}

      {/* Zone labels */}
      {zone_labels.map((z) => (
        <text
          key={`label-${z.zone}`}
          x={cellX(z.x_start) + ((z.x_end - z.x_start + 1) * CELL) / 2}
          y={cellY(1) - 6}
          textAnchor="middle"
          fontSize={11}
          fontWeight="700"
          fill="#64748b"
          letterSpacing="0.05em"
        >
          ZONE {z.zone}
        </text>
      ))}

      {/* Dock cells (row 0) */}
      {[
        { code: "DOCK-IN",  coord: layout.dock_in,  label: "DOCK IN",  fill: "#bfdbfe" },
        { code: "DOCK-OUT", coord: layout.dock_out, label: "DOCK OUT", fill: "#bbf7d0" },
      ].map(({ code, coord, label, fill }) => (
        <g key={code}>
          <rect
            x={cellX(coord.x) + 1}
            y={cellY(coord.y) + 1}
            width={CELL - 2}
            height={CELL - 2}
            rx={6}
            fill={fill}
            stroke="#94a3b8"
            strokeWidth={1.5}
          />
          <text
            x={cellX(coord.x) + HALF}
            y={cellY(coord.y) + HALF - 4}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={8}
            fontWeight="600"
            fill="#1e3a5f"
          >
            {label}
          </text>
        </g>
      ))}

      {/* Storage cells */}
      {storageEntries.map(([code, coord]) => (
        <g key={code}>
          <rect
            x={cellX(coord.x) + 1}
            y={cellY(coord.y) + 1}
            width={CELL - 2}
            height={CELL - 2}
            rx={4}
            fill="white"
            stroke="#cbd5e1"
            strokeWidth={1}
          />
          <text
            x={cellX(coord.x) + HALF}
            y={cellY(coord.y) + HALF}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={8}
            fill="#475569"
          >
            {code}
          </text>
        </g>
      ))}

      {/* Station cells */}
      {Object.entries(stations).map(([sid, coord]) => (
        <g key={sid}>
          <rect
            x={cellX(coord.x) + 1}
            y={cellY(coord.y) + 1}
            width={CELL - 2}
            height={CELL - 2}
            rx={6}
            fill="#e0e7ff"
            stroke="#818cf8"
            strokeWidth={1.5}
          />
          <text
            x={cellX(coord.x) + HALF}
            y={cellY(coord.y) + HALF - 4}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={8}
            fontWeight="600"
            fill="#3730a3"
          >
            {sid}
          </text>
          <text
            x={cellX(coord.x) + HALF}
            y={cellY(coord.y) + HALF + 8}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={7}
            fill="#4338ca"
          >
            STATION
          </text>
        </g>
      ))}

      {/* AMR icons */}
      {amrs.map((amr) => {
        const cx = cellX(amr.x) + HALF;
        const cy = cellY(amr.y) + HALF;
        const fill = STATUS_COLORS[amr.status] ?? "#94a3b8";
        return (
          <g
            key={amr.id}
            style={{
              transform: `translate(${cx}px, ${cy}px)`,
              transition: "transform 0.1s linear",
            }}
          >
            {/* Shadow */}
            <circle r={HALF * 0.45} fill="rgba(0,0,0,0.15)" cy={3} />
            {/* Body */}
            <circle r={HALF * 0.42} fill={fill} stroke="white" strokeWidth={2} />
            {/* Direction indicator dot */}
            <circle r={3} fill="white" cy={-(HALF * 0.42) + 6} />
            {/* Name label */}
            <text
              y={-(HALF * 0.42) - 6}
              textAnchor="middle"
              fontSize={9}
              fontWeight="700"
              fill="#1e293b"
              style={{ pointerEvents: "none" }}
            >
              {amr.name}
            </text>
          </g>
        );
      })}

      {/* Target lines for traveling AMRs */}
      {amrs
        .filter((a) => a.status === "traveling" && a.target_x !== null && a.target_y !== null)
        .map((amr) => (
          <line
            key={`target-${amr.id}`}
            x1={cellX(amr.x) + HALF}
            y1={cellY(amr.y) + HALF}
            x2={cellX(amr.target_x!) + HALF}
            y2={cellY(amr.target_y!) + HALF}
            stroke={STATUS_COLORS.traveling}
            strokeWidth={1}
            strokeDasharray="4 4"
            opacity={0.5}
          />
        ))}
    </svg>
  );
}
