import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface Props {
  chart: string;
  id?: string;
}

mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  themeVariables: {
    primaryColor: '#6366f1',
    primaryTextColor: '#000000',
    primaryBorderColor: '#818cf8',
    lineColor: '#6b70a0',
    secondaryColor: '#252840',
    tertiaryColor: '#1e2035',
    fontFamily: 'Inter, sans-serif',
    fontSize: '14px',
    nodeBorder: '#818cf8',
    nodeTextColor: '#000000',
    edgeLabelBackground: '#1e2035',
    clusterBkg: '#1e2035',
  },
  flowchart: {
    curve: 'basis',
    padding: 20,
  },
});

export default function MermaidDiagram({ chart, id = 'mermaid-diagram' }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chart || !containerRef.current) return;

    const renderChart = async () => {
      try {
        containerRef.current!.innerHTML = '';
        const { svg } = await mermaid.render(id, chart);
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (err) {
        console.error('Mermaid render error:', err);
        if (containerRef.current) {
          containerRef.current.innerHTML = `<pre style="color: #9da2c2; font-size: 12px;">${chart}</pre>`;
        }
      }
    };

    renderChart();
  }, [chart, id]);

  return <div className="mermaid-container" ref={containerRef} />;
}
