// src/pages/EventosPage.jsx

import { useState, useEffect, useRef, useCallback } from "react"
import { Link } from "react-router-dom"
import StatusButtons from "../components/StatusButtons"
import CityFilter from "../components/CityFilter"
import DateFilter from "../components/DateFilter"
import { supabase } from "../supabaseClient"
import { API_URL } from "../config"

const EVENTOS_POR_PAGINA = 60

function EventosPage({ sessao }) {

  // ─── ESTADOS ───────────────────────────────────────────────

  const [eventos, setEventos] = useState([])
  const [carregandoInicial, setCarregandoInicial] = useState(true)
  const [carregandoMais, setCarregandoMais] = useState(false)
  const [temMais, setTemMais] = useState(true)

  const [cidadeSelecionada, setCidadeSelecionada] = useState("Todas")
  const [periodoSelecionado, setPeriodoSelecionado] = useState("")
  const [statusMap, setStatusMap] = useState({})

  // Contagens vindas do backend — independentes da lista de eventos
  // carregada, já que agora o filtro roda no servidor
  const [resumoCidades, setResumoCidades] = useState([])
  const [resumoPeriodos, setResumoPeriodos] = useState([])

  const sentinelaRef = useRef(null)


  // ─── AUTENTICAÇÃO ────────────────────────────────────────────

  async function entrarComGoogle() {
    await supabase.auth.signInWithOAuth({ provider: "google" })
  }

  async function sair() {
    await supabase.auth.signOut()
    setStatusMap({}) // limpa status ao deslogar, já que eram do usuário anterior
  }


  // ─── BUSCA DE EVENTOS (paginada, com filtro no backend) ─────

  const buscarEventos = useCallback(async (skipAtual, substituirLista) => {
    if (substituirLista) {
      setCarregandoInicial(true)
    } else {
      setCarregandoMais(true)
    }

    const params = new URLSearchParams()
    if (cidadeSelecionada !== "Todas") params.set("city", cidadeSelecionada)
    if (periodoSelecionado !== "") params.set("periodo", periodoSelecionado)
    params.set("skip", skipAtual)
    params.set("limit", EVENTOS_POR_PAGINA)

    const resposta = await fetch(`${API_URL}/events/?${params.toString()}`)
    const dados = await resposta.json()

    setEventos(anterior => substituirLista ? dados : [...anterior, ...dados])
    setTemMais(dados.length === EVENTOS_POR_PAGINA)
    setCarregandoInicial(false)
    setCarregandoMais(false)
  }, [cidadeSelecionada, periodoSelecionado])

  // Sempre que o filtro de cidade ou período muda, recomeça do zero
  useEffect(() => {
    buscarEventos(0, true)
  }, [buscarEventos])

  // Busca as contagens (para os atalhos/dropdowns) uma vez, na entrada da página
  useEffect(() => {
    fetch(`${API_URL}/events/resumo-filtros/`)
      .then(r => r.json())
      .then(dados => {
        setResumoCidades(dados.cidades)
        setResumoPeriodos(dados.periodos)
      })
  }, [])

  // Status só é buscado se o usuário estiver logado
  useEffect(() => {
    if (!sessao) {
      setStatusMap({})
      return
    }

    fetch(`${API_URL}/status/`, {
      headers: {
        Authorization: `Bearer ${sessao.access_token}`
      }
    })
      .then(r => r.json())
      .then(dadosStatus => {
        const mapa = {}
        dadosStatus.forEach(s => { mapa[s.event_id] = s.status })
        setStatusMap(mapa)
      })
  }, [sessao])


  // ─── SCROLL INFINITO ─────────────────────────────────────────

  useEffect(() => {
    const sentinela = sentinelaRef.current
    if (!sentinela) return

    const observer = new IntersectionObserver(
      (entradas) => {
        const [entrada] = entradas
        if (entrada.isIntersecting && temMais && !carregandoMais && !carregandoInicial) {
          buscarEventos(eventos.length, false)
        }
      },
      { rootMargin: "300px" } // começa a carregar um pouco antes de chegar ao fim de verdade
    )

    observer.observe(sentinela)
    return () => observer.disconnect()
  }, [temMais, carregandoMais, carregandoInicial, eventos.length, buscarEventos])


  // ─── ATUALIZAÇÃO DE STATUS ─────────────────────────────────

  function atualizarStatus(eventoId, novoStatus) {
    setStatusMap(anterior => ({
      ...anterior,
      [eventoId]: novoStatus
    }))
  }


  // ─── FORMATAÇÃO ──────────────────────────────────────────────

  function formatarData(dataISO) {
    return new Date(dataISO).toLocaleString("pt-BR", {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    })
  }


  // ─── TELA DE LOADING INICIAL ─────────────────────────────────

  if (carregandoInicial) {
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
      <div className="flex justify-between items-start mb-2">
        <div>
          <h1 className="text-3xl font-bold text-white">🎵 BeatMap</h1>
          <p className="text-gray-400">{eventos.length} evento(s) carregado(s)</p>
        </div>

        {/* Link para Minhas Interações + Indicador de login no topo */}
        <div className="flex items-center gap-4">
          <Link to="/minhas-interacoes" className="text-sm text-gray-300 hover:text-white underline">
            🎟️ Minhas Interações
          </Link>

          {sessao ? (
            <div className="flex items-center gap-3">
              {sessao.user.user_metadata?.avatar_url && (
                <img
                  src={sessao.user.user_metadata.avatar_url}
                  alt="Avatar"
                  className="w-8 h-8 rounded-full"
                />
              )}
              <span className="text-gray-300 text-sm">
                Olá, {sessao.user.user_metadata?.full_name || sessao.user.email}
              </span>
              <button
                onClick={sair}
                className="text-xs text-gray-400 hover:text-white underline"
              >
                Sair
              </button>
            </div>
          ) : (
            <button
              onClick={entrarComGoogle}
              className="text-sm text-gray-300 hover:text-white underline"
            >
              Entrar com Google
            </button>
          )}
        </div>
      </div>

      {/* Filtro por cidade */}
      <p className="text-gray-500 text-xs uppercase tracking-widest mb-2 mt-6">Cidade</p>
      <CityFilter
        cidades={resumoCidades}
        cidadeSelecionada={cidadeSelecionada}
        aoSelecionar={setCidadeSelecionada}
      />

      {/* Filtro por mês */}
      <p className="text-gray-500 text-xs uppercase tracking-widest mb-2 mt-6">Data</p>
      <DateFilter
        periodos={resumoPeriodos}
        periodoSelecionado={periodoSelecionado}
        aoSelecionar={setPeriodoSelecionado}
      />

      {/* Grid de cards */}
      {eventos.length === 0 ? (
        <p className="text-gray-500 mt-8">Nenhum evento encontrado com esse filtro.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
          {eventos.map(evento => (
            <div
              key={evento.id}
              className="bg-gray-800 rounded-xl p-5 border border-gray-700"
            >
              <h2 className="text-white font-semibold text-lg mb-2">
                {evento.name}
              </h2>

              <p className="text-purple-400 text-sm mb-1">
                📍 {evento.venue?.name} — {evento.venue?.city}/{evento.venue?.state}
              </p>

              <p className="text-gray-400 text-sm mb-1">
                📅 {formatarData(evento.event_date)}
              </p>

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

              <StatusButtons
                eventoId={evento.id}
                statusAtual={statusMap[evento.id]}
                aoAtualizar={atualizarStatus}
                sessao={sessao}
                aoExigirLogin={entrarComGoogle}
              />
            </div>
          ))}
        </div>
      )}

      {/* Sentinela do scroll infinito — invisível, só serve de gatilho */}
      <div ref={sentinelaRef} className="h-4" />

      {carregandoMais && (
        <p className="text-gray-500 text-center mt-6">Carregando mais eventos...</p>
      )}

      {!temMais && eventos.length > 0 && (
        <p className="text-gray-600 text-center text-sm mt-6">
          Isso é tudo por aqui — {eventos.length} evento(s) no total com esse filtro.
        </p>
      )}

    </div>
  )
}

export default EventosPage