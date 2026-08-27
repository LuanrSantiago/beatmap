import { useState, useRef, useEffect } from "react"

const CIDADE_FIXA = "Nova Lima"
const QTD_DESTAQUE = 5 // total de cidades no destaque, incluindo a fixa

function CityFilter({ cidades, cidadeSelecionada, aoSelecionar }) {
  const [busca, setBusca] = useState("")
  const [aberto, setAberto] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    function aoClicarFora(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setAberto(false)
      }
    }
    document.addEventListener("mousedown", aoClicarFora)
    return () => document.removeEventListener("mousedown", aoClicarFora)
  }, [])

  // ─── Contagem por cidade, vinda do backend ─────────────────
  const contagem = {}
  cidades.forEach(c => { contagem[c.cidade] = c.total })

  // Garante que a cidade fixa sempre exista, mesmo com 0 eventos
  if (!(CIDADE_FIXA in contagem)) {
    contagem[CIDADE_FIXA] = 0
  }

  const todasCidades = Object.keys(contagem).sort((a, b) =>
    a.localeCompare(b, "pt-BR")
  )

  // ─── Cidades em destaque (atalhos fixos) ───────────────────
  const outrasPorVolume = Object.entries(contagem)
    .filter(([cidade]) => cidade !== CIDADE_FIXA)
    .sort((a, b) => b[1] - a[1])
    .slice(0, QTD_DESTAQUE - 1)
    .map(([cidade]) => cidade)

  const destaque = [...outrasPorVolume, CIDADE_FIXA].sort((a, b) =>
    a.localeCompare(b, "pt-BR")
  )

  // ─── Lista filtrada pela busca no dropdown ─────────────────
  const cidadesFiltradas = todasCidades.filter(c =>
    c.toLowerCase().includes(busca.toLowerCase())
  )

  function selecionar(cidade) {
    aoSelecionar(cidade)
    setBusca("")
    setAberto(false)
  }

  return (
    <div>
      {/* Atalhos: Todas + destaque */}
      <div className="flex flex-wrap gap-2 mb-3">
        <button
          onClick={() => selecionar("Todas")}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
            ${cidadeSelecionada === "Todas"
              ? "bg-purple-600 text-white"
              : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
        >
          Todas
        </button>

        {destaque.map(cidade => (
          <button
            key={cidade}
            onClick={() => selecionar(cidade)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
              ${cidadeSelecionada === cidade
                ? "bg-purple-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
          >
            {cidade} ({contagem[cidade]})
          </button>
        ))}
      </div>

      {/* Dropdown pesquisável com todas as cidades */}
      <div className="relative w-64" ref={containerRef}>
        <input
          type="text"
          placeholder="Buscar outra cidade..."
          value={busca}
          onFocus={() => setAberto(true)}
          onChange={e => {
            setBusca(e.target.value)
            setAberto(true)
          }}
          className="w-full bg-gray-800 text-gray-300 text-sm rounded-lg px-4 py-2 border border-gray-700 focus:outline-none focus:border-purple-500"
        />

        {aberto && (
          <div className="absolute z-10 mt-1 w-full max-h-60 overflow-y-auto bg-gray-800 border border-gray-700 rounded-lg shadow-lg">
            {cidadesFiltradas.length === 0 && (
              <p className="px-4 py-2 text-gray-500 text-sm">Nenhuma cidade encontrada</p>
            )}
            {cidadesFiltradas.map(cidade => (
              <button
                key={cidade}
                onClick={() => selecionar(cidade)}
                className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-700
                  ${cidadeSelecionada === cidade ? "text-purple-400" : "text-gray-300"}`}
              >
                {cidade} ({contagem[cidade]})
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default CityFilter