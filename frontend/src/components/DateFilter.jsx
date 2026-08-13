import { useState, useRef, useEffect } from "react"

const QTD_DESTAQUE = 3 // mês atual + próximos 2

const NOMES_MES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

function formatarPeriodo(periodo) {
  if (periodo === "") return "Todos"
  const [mes, ano] = periodo.split("/")
  return `${NOMES_MES[parseInt(mes) - 1]} ${ano}`
}

function DateFilter({ eventos, periodoSelecionado, aoSelecionar }) {
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

  // ─── Contagem de eventos por período ───────────────────────
  const contagem = {}
  eventos.forEach(e => {
    const d = new Date(e.event_date)
    const chave = `${d.getMonth() + 1}/${d.getFullYear()}`
    contagem[chave] = (contagem[chave] || 0) + 1
  })

  // ─── Períodos em destaque: mês atual + próximos QTD_DESTAQUE - 1 ───
  const hoje = new Date()
  const destaque = []
  for (let i = 0; i < QTD_DESTAQUE; i++) {
    const d = new Date(hoje.getFullYear(), hoje.getMonth() + i, 1)
    const chave = `${d.getMonth() + 1}/${d.getFullYear()}`
    if (!(chave in contagem)) contagem[chave] = 0
    destaque.push(chave)
  }

  // ─── Todos os períodos, em ordem cronológica ───────────────
  const todosPeriodos = Object.keys(contagem).sort((a, b) => {
    const [mesA, anoA] = a.split("/").map(Number)
    const [mesB, anoB] = b.split("/").map(Number)
    return anoA - anoB || mesA - mesB
  })

  const periodosFiltrados = todosPeriodos.filter(p =>
    formatarPeriodo(p).toLowerCase().includes(busca.toLowerCase())
  )

  function selecionar(periodo) {
    aoSelecionar(periodo)
    setBusca("")
    setAberto(false)
  }

  return (
    <div>
      {/* Atalhos: Todos + destaque */}
      <div className="flex flex-wrap gap-2 mb-3">
        <button
          onClick={() => selecionar("")}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
            ${periodoSelecionado === ""
              ? "bg-purple-600 text-white"
              : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
        >
          Todos
        </button>

        {destaque.map(periodo => (
          <button
            key={periodo}
            onClick={() => selecionar(periodo)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
              ${periodoSelecionado === periodo
                ? "bg-purple-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
          >
            {formatarPeriodo(periodo)} ({contagem[periodo]})
          </button>
        ))}
      </div>

      {/* Dropdown pesquisável com todos os períodos */}
      <div className="relative w-64" ref={containerRef}>
        <input
          type="text"
          placeholder="Buscar outro período..."
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
            {periodosFiltrados.length === 0 && (
              <p className="px-4 py-2 text-gray-500 text-sm">Nenhum período encontrado</p>
            )}
            {periodosFiltrados.map(periodo => (
              <button
                key={periodo}
                onClick={() => selecionar(periodo)}
                className={`block w-full text-left px-4 py-2 text-sm hover:bg-gray-700
                  ${periodoSelecionado === periodo ? "text-purple-400" : "text-gray-300"}`}
              >
                {formatarPeriodo(periodo)} ({contagem[periodo]})
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default DateFilter