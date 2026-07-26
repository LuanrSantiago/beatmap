// src/components/StatusButtons.jsx

import { useState } from "react"
import { API_URL } from "../config"

function StatusButtons({ eventoId, statusAtual, aoAtualizar, sessao, aoExigirLogin }) {

  const [processando, setProcessando] = useState(null)

  const botoes = [
    { valor: "going",     texto: "✅ Vou",     cor: "bg-green-600"  },
    { valor: "thinking",  texto: "🤔 Talvez",  cor: "bg-yellow-600" },
    { valor: "bought",    texto: "🎟️ Comprei", cor: "bg-blue-600"   },
    { valor: "not_going", texto: "❌ Não vou", cor: "bg-red-700"    },
  ]

  async function clicarStatus(valor) {
    if (valor === statusAtual || processando) return

    // NOVO: se não está logado, dispara o login em vez de chamar a API
    if (!sessao) {
      aoExigirLogin()
      return
    }

    setProcessando(valor)

    try {
      const resposta = await fetch(`${API_URL}/status/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // NOVO: token do usuário logado, pra API saber quem está marcando
          Authorization: `Bearer ${sessao.access_token}`,
        },
        body: JSON.stringify({ event_id: eventoId, status: valor }),
      })

      if (resposta.ok) {
        aoAtualizar(eventoId, valor)
      }
    } catch (erro) {
      console.error("Erro ao atualizar status:", erro)
    } finally {
      setProcessando(null)
    }
  }

  return (
    <div className="flex flex-wrap gap-2 mt-4">
      {botoes.map(botao => {
        const estaAtivo      = statusAtual === botao.valor
        const estaCarregando = processando === botao.valor

        return (
          <button
            key={botao.valor}
            onClick={() => clicarStatus(botao.valor)}
            disabled={!!processando}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-all
              ${estaAtivo
                ? `${botao.cor} text-white scale-105 ring-2 ring-white/30`
                : "bg-gray-700 text-gray-400 hover:bg-gray-600"
              }
              ${estaCarregando ? "opacity-60 cursor-wait" : ""}
              ${processando && !estaCarregando ? "opacity-40 cursor-not-allowed" : ""}
            `}
          >
            {estaCarregando ? "..." : botao.texto}
          </button>
        )
      })}
    </div>
  )
}

export default StatusButtons