import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as d3 from 'd3'
import { usersApi, type GraphEdge, type GraphNode } from '../api/users'

type SimNode = GraphNode & d3.SimulationNodeDatum
type SimEdge = { source: SimNode; target: SimNode; type: GraphEdge['type'] }

const NODE_COLOR: Record<GraphNode['type'], string> = {
  book:   '#7c6af7',
  author: '#f97316',
  genre:  '#22c55e',
}

const NODE_RADIUS: Record<GraphNode['type'], number> = {
  book:   22,
  author: 16,
  genre:  12,
}

export default function KnowledgeGraphPage() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [status, setStatus] = useState<'loading' | 'empty' | 'ready'>('loading')
  const navigate = useNavigate()

  useEffect(() => {
    let cancelled = false

    async function draw() {
      const data = await usersApi.getKnowledgeGraph()
      if (cancelled) return

      if (data.nodes.length === 0) {
        setStatus('empty')
        return
      }

      const svg = d3.select(svgRef.current!)
      svg.selectAll('*').remove()

      const width = svgRef.current!.clientWidth || window.innerWidth
      const height = svgRef.current!.clientHeight || window.innerHeight

      // Zoom + pan container
      const g = svg.append('g')
      svg.call(
        d3.zoom<SVGSVGElement, unknown>()
          .scaleExtent([0.2, 4])
          .on('zoom', (event) => g.attr('transform', event.transform))
      )

      const nodes: SimNode[] = data.nodes.map((n) => ({ ...n }))
      const nodeById = new Map(nodes.map((n) => [n.id, n]))

      const edges: SimEdge[] = data.edges
        .map((e) => ({
          source: nodeById.get(typeof e.source === 'string' ? e.source : (e.source as SimNode).id)!,
          target: nodeById.get(typeof e.target === 'string' ? e.target : (e.target as SimNode).id)!,
          type: e.type,
        }))
        .filter((e) => e.source && e.target)

      // Force simulation
      const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink<SimNode, SimEdge>(edges).id((d) => d.id).distance(90))
        .force('charge', d3.forceManyBody().strength(-350))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius((d) => NODE_RADIUS[(d as SimNode).type] + 8))

      // Edges
      const link = g.append('g')
        .selectAll('line')
        .data(edges)
        .join('line')
        .attr('stroke', '#ffffff18')
        .attr('stroke-width', 1.5)

      // Node groups
      const node = g.append('g')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .attr('cursor', (d) => d.type === 'book' ? 'pointer' : 'default')
        .call(
          d3.drag<SVGGElement, SimNode>()
            .on('start', (event, d) => {
              if (!event.active) simulation.alphaTarget(0.3).restart()
              d.fx = d.x; d.fy = d.y
            })
            .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
            .on('end', (event, d) => {
              if (!event.active) simulation.alphaTarget(0)
              d.fx = null; d.fy = null
            })
        )
        .on('click', (_, d) => { if (d.type === 'book' && d.book_id) navigate(`/books/${d.book_id}`) })

      // Book nodes — show cover if available, else circle
      node.filter((d) => d.type === 'book').each(function (d) {
        const el = d3.select(this)
        const r = NODE_RADIUS.book
        if (d.cover_url) {
          const clipId = `clip-${d.id}`
          svg.append('defs').append('clipPath').attr('id', clipId)
            .append('circle').attr('r', r)
          el.append('image')
            .attr('href', d.cover_url)
            .attr('x', -r).attr('y', -r)
            .attr('width', r * 2).attr('height', r * 2)
            .attr('clip-path', `url(#${clipId})`)
            .attr('preserveAspectRatio', 'xMidYMid slice')
        } else {
          el.append('circle').attr('r', r).attr('fill', NODE_COLOR.book)
        }
      })

      // Author + genre nodes
      node.filter((d) => d.type !== 'book')
        .append('circle')
        .attr('r', (d) => NODE_RADIUS[d.type])
        .attr('fill', (d) => NODE_COLOR[d.type])
        .attr('opacity', 0.85)

      // Labels
      node.append('text')
        .text((d) => d.label.length > 18 ? d.label.slice(0, 16) + '…' : d.label)
        .attr('text-anchor', 'middle')
        .attr('dy', (d) => NODE_RADIUS[d.type] + 12)
        .attr('font-size', (d) => d.type === 'book' ? 10 : 9)
        .attr('fill', '#e2e8f0')
        .attr('pointer-events', 'none')

      simulation.on('tick', () => {
        link
          .attr('x1', (d) => (d.source as SimNode).x!)
          .attr('y1', (d) => (d.source as SimNode).y!)
          .attr('x2', (d) => (d.target as SimNode).x!)
          .attr('y2', (d) => (d.target as SimNode).y!)
        node.attr('transform', (d) => `translate(${d.x},${d.y})`)
      })

      setStatus('ready')
    }

    draw().catch(() => setStatus('empty'))
    return () => { cancelled = true }
  }, [navigate])

  return (
    <div className="relative w-full h-screen bg-surface-card overflow-hidden">
      {/* Legend */}
      {status === 'ready' && (
        <div className="absolute top-4 left-4 z-10 flex flex-col gap-1.5 bg-surface-raised/80 backdrop-blur border border-border rounded-xl p-3">
          {(['book', 'author', 'genre'] as GraphNode['type'][]).map((type) => (
            <div key={type} className="flex items-center gap-2 text-xs text-text-secondary capitalize">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full"
                style={{ background: NODE_COLOR[type] }}
              />
              {type}
            </div>
          ))}
        </div>
      )}

      {status === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full border-2 border-brand border-t-transparent animate-spin" />
        </div>
      )}

      {status === 'empty' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 text-text-secondary">
          <p className="text-sm">Add books to your Already Read shelf to see your knowledge graph.</p>
        </div>
      )}

      {/* D3 owns everything inside this svg */}
      <svg ref={svgRef} className="w-full h-full" />
    </div>
  )
}
