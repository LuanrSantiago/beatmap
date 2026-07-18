// src/pages/EventosPage.jsx

import { useState, useEffect } from "react"
import StatusButtons from "../components/StatusButtons"

function EventosPage() {

  // ─── ESTADOS ───────────────────────────────────────────────

  const [eventos, setEventos] = useState([])
  const [carregando, setCarregando] = useState(true)
  const [cidadeSelecionada, setCidadeSelecionada] = useState("Todas")

  // NOVO (item 4): filtro por mês
  // 0 = todos os meses
  const [periodoSelecionado, setPeriodoSelecionado] = useState("")

  const [statusMap, setStatusMap] = useState({})


  // ─── BUSCA DE DADOS ────────────────────────────────────────

  useEffect(() => {
    Promise.all([
      fetch("http://127.0.0.1:8000/events/?limit=200").then(r => r.json()),
      fetch("http://127.0.0.1:8000/status/").then(r => r.json()),
    ]).then(([dadosEventos, dadosStatus]) => {

      // ITEM 2: ordena eventos por data antes de salvar no estado
      // sort() compara dois elementos (a, b):
      //   retorno negativo = a vem antes de b
      //   retorno positivo = b vem antes de a
      const ordenados = dadosEventos.sort(
        (a, b) => new Date(a.event_date) - new Date(b.event_date)
      )

      setEventos(ordenados)

      const mapa = {}
      dadosStatus.forEach(s => { mapa[s.event_id] = s.status })
      setStatusMap(mapa)

      setCarregando(false)
    })
  }, [])


  // ─── ATUALIZAÇÃO DE STATUS ─────────────────────────────────

  function atualizarStatus(eventoId, novoStatus) {
    setStatusMap(anterior => ({
      ...anterior,
      [eventoId]: novoStatus
    }))
  }


  // ─── LÓGICA DE FILTRO ──────────────────────────────────────

  // Cidades únicas
  const cidades = [
    "Todas",
    ...new Set(eventos.map(e => e.venue?.city).filter(Boolean))
  ]

  // NOVO (item 4): meses com eventos disponíveis
  // Extrai só os meses que realmente têm eventos (sem repetir)
  // Gera lista de "Jul 2026", "Ago 2026"... sem repetir
  const periodos = ["", ...new Set(
    eventos.map(e => {
      const d = new Date(e.event_date)
      return `${d.getMonth() + 1}/${d.getFullYear()}`
    })
  )]
  
  function formatarPeriodo(periodo) {
    if (periodo === "") return "Todos"
    const [mes, ano] = periodo.split("/")
    const nomes = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    return `${nomes[parseInt(mes) - 1]} ${ano}`
  }
  
  const eventosFiltrados = eventos
    .filter(e => cidadeSelecionada === "Todas" || e.venue?.city === cidadeSelecionada)
    .filter(e => {
      if (periodoSelecionado === "") return true
      const d = new Date(e.event_date)
      return `${d.getMonth() + 1}/${d.getFullYear()}` === periodoSelecionado
    })

  // ─── FORMATAÇÃO DE DATA (item 1) ───────────────────────────
    // Mostra data E horário no card
    // Antes: toLocaleDateString → "18/07/2026"
    // Agora: toLocaleString    → "18/07/2026, 22:00"

  function formatarData(dataISO) {
    return new Date(dataISO).toLocaleString("pt-BR", {
      day:   "2-digit",
      month: "2-digit",
      year:  "numeric",
      hour:  "2-digit",
      minute: "2-digit",
    })
  }


  // ─── TELA DE LOADING ───────────────────────────────────────

  if (carregando) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <p className="text-white text-xl">Carregando eventos...</p>
      </div>
    )
  }


  // ─── TELA PRINCIPAL ────────────────────────────────────────

  return (
    <div className="bg-gray-900 min-h-screen p-8">

      {/* Cabeçalho */}
      <h1 className="text-3xl font-bold text-white mb-2">🎵 BeatMap</h1>
      <p className="text-gray-400 mb-6">{eventosFiltrados.length} eventos encontrados</p>

      {/* Filtro por cidade */}
      <p className="text-gray-500 text-xs uppercase tracking-widest mb-2">Cidade</p>
      <div className="flex flex-wrap gap-2 mb-6">
        {cidades.map(cidade => (
          <button
            key={cidade}
            onClick={() => setCidadeSelecionada(cidade)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
              ${cidadeSelecionada === cidade
                ? "bg-purple-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
          >
            {cidade}
          </button>
        ))}
      </div>

      {/* NOVO: Filtro por mês (item 4) */}
       <p className="text-gray-500 text-xs uppercase tracking-widest mb-2">Data</p>
       <select
         value={periodoSelecionado}
         onChange={e => setPeriodoSelecionado(e.target.value)}
         className="mb-8 bg-gray-800 text-gray-300 text-sm rounded-lg px-4 py-2 border border-gray-700 focus:outline-none focus:border-purple-500"
       >
         {periodos.map(p => (
           <option key={p} value={p}>{formatarPeriodo(p)}</option>
         ))}
       </select>

      {/* Grid de cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {eventosFiltrados.map(evento => (
          <div
            key={evento.id}
            className="bg-gray-800 rounded-xl p-5 border border-gray-700"
          >
            {/* Nome */}
            <h2 className="text-white font-semibold text-lg mb-2">
              {evento.name}
            </h2>

            {/* Local */}
            <p className="text-purple-400 text-sm mb-1">
              📍 {evento.venue?.name} — {evento.venue?.city}/{evento.venue?.state}
            </p>

            {/* Data com horário (item 1) */}
            <p className="text-gray-400 text-sm mb-1">
              📅 {formatarData(evento.event_date)}
            </p>

            {/* Link de ingressos */}
            {evento.ticket_url && (
              <a
                href={evento.ticket_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-purple-400 text-xs hover:underline"
              >
                🎟️ Ver ingressos
              </a>
            )}

            {/* Botões de status com feedback visual (item 3) */}
            <StatusButtons
              eventoId={evento.id}
              statusAtual={statusMap[evento.id]}
              aoAtualizar={atualizarStatus}
            />
          </div>
        ))}
      </div>

    </div>
  )
}

export default EventosPage