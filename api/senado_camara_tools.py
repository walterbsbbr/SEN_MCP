"""
Ferramentas para APIs Públicas do Senado Federal e Câmara dos Deputados
Versão adaptada para Vercel (sem dependência de MCP stdio)
"""
import requests
import xml.etree.ElementTree as ET


def _call_api(base_url: str, endpoint: str, params: dict = None) -> dict:
    """
    Função auxiliar para chamar APIs públicas brasileiras (JSON - Câmara).

    Args:
        base_url: URL base da API
        endpoint: Endpoint específico
        params: Parâmetros query string

    Returns:
        Resposta da API em formato dict
    """
    url = f"{base_url}{endpoint}"

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        # Tenta parsear como JSON
        try:
            data = response.json()
            return {"success": True, "status_code": response.status_code, "data": data}
        except:
            # Se não for JSON, retorna texto
            return {"success": True, "status_code": response.status_code, "data": response.text}

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Erro ao chamar API: {str(e)}"
        }


def _call_senado_api(endpoint: str, format_json: bool = True) -> dict:
    """
    Função auxiliar para chamar APIs do Senado (retorna XML ou JSON).

    Args:
        endpoint: Endpoint específico (ex: "/senador/lista/atual" ou "/comissao/40")
        format_json: Se True, adiciona .json ao endpoint

    Returns:
        Resposta da API parseada
    """
    base_url = "https://legis.senado.leg.br/dadosabertos"

    # Adiciona .json se solicitado
    if format_json and not endpoint.endswith('.json'):
        endpoint = endpoint + '.json'

    url = f"{base_url}{endpoint}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Se solicitou JSON
        if format_json or endpoint.endswith('.json'):
            try:
                data = response.json()
                return {"success": True, "status_code": response.status_code, "data": data}
            except:
                pass

        # Tenta parsear como XML
        try:
            root = ET.fromstring(response.content)
            # Converte XML para dict básico
            xml_data = {"xml_root": root.tag, "data": response.text}
            return {"success": True, "status_code": response.status_code, "data": xml_data}
        except:
            # Retorna texto bruto
            return {"success": True, "status_code": response.status_code, "data": response.text}

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Erro ao chamar API do Senado: {str(e)}"
        }


# ========================================
# SENADO FEDERAL
# ========================================

def buscar_senadores(uf: str = None) -> dict:
    """
    Lista senadores em exercício, opcionalmente filtrados por UF.

    Args:
        uf: Sigla do estado (ex: "SP", "RJ", "MG") ou None para todos

    Returns:
        Lista de senadores com informações completas
    """
    endpoint = "/senador/lista/atual"
    if uf:
        endpoint += f"?uf={uf.upper()}"

    return _call_senado_api(endpoint, format_json=True)


def buscar_proposicoes_senado(sigla: str, ano: str = None) -> dict:
    """
    Busca proposições no Senado por tipo e ano.

    Args:
        sigla: Tipo da proposição (ex: "PEC", "PL", "PLS", "MPV")
        ano: Ano da proposição (ex: "2024", "2025")

    Returns:
        Lista de proposições encontradas
    """
    endpoint = f"/proposicao/sigla/{sigla.upper()}"
    if ano:
        endpoint += f"/ano/{ano}"

    return _call_senado_api(endpoint, format_json=True)


def detalhes_proposicao_senado(codigo: str) -> dict:
    """
    Obtém detalhes completos de uma proposição do Senado.

    Args:
        codigo: Código da proposição (ex: "132046")

    Returns:
        Detalhes da proposição incluindo ementa, autoria, tramitação
    """
    return _call_senado_api(f"/proposicao/{codigo}", format_json=True)


def votacoes_senado(data_inicio: str, data_fim: str = None) -> dict:
    """
    Lista votações do Senado em um período.

    Args:
        data_inicio: Data inicial no formato AAAAMMDD (ex: "20250101")
        data_fim: Data final no formato AAAAMMDD (opcional)

    Returns:
        Lista de votações realizadas no período
    """
    endpoint = f"/plenario/votacao/lista/data/{data_inicio}"
    if data_fim:
        endpoint += f"/data/{data_fim}"

    return _call_senado_api(endpoint, format_json=True)


def listar_comissoes_senado(tipo: str = "permanente") -> dict:
    """
    Lista comissões do Senado Federal.

    Args:
        tipo: Tipo da comissão - "permanente", "cpi", "temporaria", "orgaos" (padrão: "permanente")

    Returns:
        Lista de comissões com códigos e nomes em formato XML
    """
    # Normaliza o tipo
    tipo_lower = tipo.lower()

    # Mapeia tipos comuns
    tipo_map = {
        "permanente": "permanente",
        "cpi": "cpi",
        "temporaria": "temporaria",
        "temporária": "temporaria",
        "orgaos": "orgaos",
        "órgãos": "orgaos",
        "orgao": "orgaos"
    }

    tipo_final = tipo_map.get(tipo_lower, "permanente")
    endpoint = f"/comissao/lista/{tipo_final}"

    return _call_senado_api(endpoint, format_json=False)


def detalhes_comissao_senado(codigo: str) -> dict:
    """
    Obtém detalhes de uma comissão do Senado.

    Args:
        codigo: Código numérico da comissão (ex: "40" para CAS, "38" para CAE, "34" para CCJ)

    Returns:
        Detalhes da comissão incluindo composição e atribuições
    """
    endpoint = f"/comissao/{codigo}"
    return _call_senado_api(endpoint, format_json=False)


def membros_comissao_senado(codigo: str) -> dict:
    """
    Lista membros de uma comissão do Senado.

    Args:
        codigo: Código da comissão

    Returns:
        Lista de senadores membros com cargos (presidente, vice, etc)
    """
    return _call_api(
        base_url="https://legis.senado.leg.br/dadosabertos",
        endpoint=f"/comissao/{codigo}/membros"
    )


def reunioes_comissao_senado(codigo: str, data_inicio: str = None, data_fim: str = None) -> dict:
    """
    Lista reuniões de uma comissão do Senado.

    Args:
        codigo: Código da comissão
        data_inicio: Data inicial no formato AAAAMMDD (opcional)
        data_fim: Data final no formato AAAAMMDD (opcional)

    Returns:
        Lista de reuniões com pautas e resultados
    """
    endpoint = f"/comissao/{codigo}/reunioes"
    params = {}

    if data_inicio:
        params['dataInicio'] = data_inicio
    if data_fim:
        params['dataFim'] = data_fim

    return _call_api(
        base_url="https://legis.senado.leg.br/dadosabertos",
        endpoint=endpoint,
        params=params
    )


def buscar_agenda_comissao(data_inicio: str, data_fim: str = None) -> dict:
    """
    Busca a agenda de comissões do Senado em um período para encontrar códigos de reuniões.
    Use esta função ANTES de buscar detalhes de uma reunião específica.

    Args:
        data_inicio: Data inicial no formato YYYYMMDD (ex: "20251209")
        data_fim: Data final no formato YYYYMMDD (ex: "20251211"). Se omitido, usa data_inicio

    Returns:
        Lista de reuniões agendadas com seus códigos
    """
    if not data_fim:
        data_fim = data_inicio

    endpoint = f"/comissao/agenda/{data_inicio}/{data_fim}"

    return _call_senado_api(endpoint, format_json=True)


def detalhes_reuniao_comissao(codigo_reuniao: str) -> dict:
    """
    Obtém detalhes completos de uma reunião específica de comissão pelo código.
    Use buscar_agenda_comissao() primeiro para encontrar o código da reunião.

    Args:
        codigo_reuniao: Código da reunião obtido via buscar_agenda_comissao

    Returns:
        Detalhes completos da reunião incluindo pauta, participantes e resultados
    """
    endpoint = f"/comissao/reuniao/{codigo_reuniao}"

    return _call_senado_api(endpoint, format_json=True)


def videos_reuniao_comissao(codigo_reuniao: str) -> dict:
    """
    Obtém os vídeos (Unidades Descritivas) de uma reunião específica de comissão.
    Use buscar_agenda_comissao() ou detalhes_reuniao_comissao() primeiro para encontrar o código da reunião.

    Args:
        codigo_reuniao: Código da reunião (ex: "72345")

    Returns:
        Lista de vídeos disponíveis da reunião
    """
    endpoint = f"/comissao/reuniao/{codigo_reuniao}/videos"

    return _call_senado_api(endpoint, format_json=True)


def agenda_senado(data: str = None) -> dict:
    """
    Obtém a agenda geral do Senado Federal (sessões plenárias).

    Args:
        data: Data no formato AAAAMMDD (ex: "20250123"). Se omitido, retorna agenda atual.

    Returns:
        Agenda de sessões, comissões e eventos
    """
    endpoint = "/agenda"
    params = {}

    if data:
        params['data'] = data

    return _call_api(
        base_url="https://legis.senado.leg.br/dadosabertos",
        endpoint=endpoint,
        params=params
    )


def materia_senado(codigo: str) -> dict:
    """
    Obtém informações completas sobre uma matéria legislativa do Senado.

    Args:
        codigo: Código da matéria (ex: "132046")

    Returns:
        Informações completas incluindo textos, tramitação, votações
    """
    return _call_api(
        base_url="https://legis.senado.leg.br/dadosabertos",
        endpoint=f"/materia/{codigo}"
    )


def autorias_senador(codigo_senador: str) -> dict:
    """
    Lista proposições de autoria de um senador.

    Args:
        codigo_senador: Código do senador

    Returns:
        Lista de proposições que o senador é autor ou coautor
    """
    return _call_api(
        base_url="https://legis.senado.leg.br/dadosabertos",
        endpoint=f"/senador/{codigo_senador}/autorias"
    )


def listar_partidos_senado() -> dict:
    """
    Obtém a lista dos Partidos Políticos em atividade e/ou extintos no Senado Federal.

    Returns:
        Lista completa de partidos políticos (ativos e extintos) do Senado
    """
    return _call_senado_api(
        endpoint="/composicao/lista/partidos"
    )


def listar_tipos_cargo_comissoes() -> dict:
    """
    Obtém a lista de Tipos de Cargo nas Comissões do Senado Federal e Congresso Nacional.

    Returns:
        Lista dos tipos de cargo (presidente, vice-presidente, titular, suplente, etc.)
    """
    return _call_senado_api(
        endpoint="/composicao/lista/tiposCargo"
    )


def mesa_diretora_congresso_nacional() -> dict:
    """
    Obtém a Composição dos integrantes da Mesa Diretora do Congresso Nacional.

    Returns:
        Composição atual da Mesa Diretora do Congresso Nacional com nomes e cargos
    """
    return _call_senado_api(
        endpoint="/composicao/mesaCN"
    )


def mesa_diretora_senado_federal() -> dict:
    """
    Obtém a Composição dos integrantes da Mesa Diretora do Senado Federal.

    Returns:
        Composição atual da Mesa Diretora do Senado Federal com nomes e cargos
    """
    return _call_senado_api(
        endpoint="/composicao/mesaSF"
    )


# ========================================
# CÂMARA DOS DEPUTADOS
# ========================================

def buscar_deputados(siglaUf: str = None, siglaPartido: str = None) -> dict:
    """
    Lista deputados em exercício, com filtros opcionais.

    Args:
        siglaUf: Sigla do estado (ex: "SP", "RJ")
        siglaPartido: Sigla do partido (ex: "PT", "PL", "PSDB")

    Returns:
        Lista de deputados com informações básicas
    """
    params = {"ordem": "ASC", "ordenarPor": "nome"}
    if siglaUf:
        params['siglaUf'] = siglaUf.upper()
    if siglaPartido:
        params['siglaPartido'] = siglaPartido.upper()

    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint="/deputados",
        params=params
    )


def detalhes_deputado(id_deputado: str) -> dict:
    """
    Obtém informações detalhadas de um deputado.

    Args:
        id_deputado: ID do deputado (obtido via buscar_deputados)

    Returns:
        Informações completas incluindo biografia, contatos, redes sociais
    """
    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint=f"/deputados/{id_deputado}"
    )


def buscar_proposicoes_camara(
    siglaTipo: str = None,
    ano: str = None,
    autor: str = None,
    keywords: str = None
) -> dict:
    """
    Busca proposições na Câmara dos Deputados.

    Args:
        siglaTipo: Tipo da proposição (ex: "PL", "PEC", "MPV")
        ano: Ano da proposição (ex: "2024")
        autor: Nome ou ID do autor
        keywords: Palavras-chave para busca

    Returns:
        Lista de proposições encontradas
    """
    params = {"ordem": "DESC", "ordenarPor": "id"}

    if siglaTipo:
        params['siglaTipo'] = siglaTipo.upper()
    if ano:
        params['ano'] = ano
    if autor:
        params['autor'] = autor
    if keywords:
        params['keywords'] = keywords

    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint="/proposicoes",
        params=params
    )


def detalhes_proposicao_camara(id_proposicao: str) -> dict:
    """
    Obtém detalhes completos de uma proposição da Câmara.

    Args:
        id_proposicao: ID da proposição (obtido via buscar_proposicoes_camara)

    Returns:
        Detalhes incluindo ementa, autoria, tramitação, textos
    """
    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint=f"/proposicoes/{id_proposicao}"
    )


def votacoes_camara(
    id_proposicao: str = None,
    dataInicio: str = None,
    dataFim: str = None
) -> dict:
    """
    Lista votações da Câmara dos Deputados.

    Args:
        id_proposicao: ID da proposição (para votações específicas)
        dataInicio: Data inicial no formato AAAA-MM-DD
        dataFim: Data final no formato AAAA-MM-DD

    Returns:
        Lista de votações com resultados e orientações partidárias
    """
    params = {"ordem": "DESC", "ordenarPor": "dataHoraRegistro"}

    if id_proposicao:
        params['idProposicao'] = id_proposicao
    if dataInicio:
        params['dataInicio'] = dataInicio
    if dataFim:
        params['dataFim'] = dataFim

    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint="/votacoes",
        params=params
    )


def despesas_deputado(id_deputado: str, ano: str, mes: str = None) -> dict:
    """
    Obtém despesas da cota parlamentar de um deputado.

    Args:
        id_deputado: ID do deputado
        ano: Ano das despesas (ex: "2024")
        mes: Mês das despesas (1-12, opcional)

    Returns:
        Lista de despesas com detalhamento
    """
    params = {"ano": ano, "ordem": "DESC", "ordenarPor": "dataDocumento"}

    if mes:
        params['mes'] = mes

    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint=f"/deputados/{id_deputado}/despesas",
        params=params
    )


def eventos_camara(dataInicio: str = None, dataFim: str = None) -> dict:
    """
    Lista eventos (reuniões, audiências) da Câmara.

    Args:
        dataInicio: Data inicial no formato AAAA-MM-DD
        dataFim: Data final no formato AAAA-MM-DD

    Returns:
        Lista de eventos programados
    """
    params = {"ordem": "ASC", "ordenarPor": "dataHoraInicio"}

    if dataInicio:
        params['dataInicio'] = dataInicio
    if dataFim:
        params['dataFim'] = dataFim

    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint="/eventos",
        params=params
    )


def listar_orgaos_camara() -> dict:
    """
    Lista todos os órgãos (comissões, frentes, etc) da Câmara.

    Returns:
        Lista de órgãos com IDs, siglas e nomes
    """
    params = {"ordem": "ASC", "ordenarPor": "sigla"}

    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint="/orgaos",
        params=params
    )


def detalhes_orgao_camara(id_orgao: str) -> dict:
    """
    Obtém detalhes de um órgão (comissão) da Câmara.

    Args:
        id_orgao: ID do órgão (obtido via listar_orgaos_camara)

    Returns:
        Detalhes do órgão incluindo composição e atribuições
    """
    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint=f"/orgaos/{id_orgao}"
    )


def membros_orgao_camara(id_orgao: str) -> dict:
    """
    Lista membros de um órgão (comissão) da Câmara.

    Args:
        id_orgao: ID do órgão

    Returns:
        Lista de deputados membros com cargos e titularidade
    """
    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint=f"/orgaos/{id_orgao}/membros"
    )


def partidos_camara() -> dict:
    """
    Lista partidos com representação na Câmara dos Deputados.

    Returns:
        Lista de partidos com siglas, nomes e número de deputados
    """
    params = {"ordem": "ASC", "ordenarPor": "sigla"}

    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint="/partidos",
        params=params
    )


def blocos_camara() -> dict:
    """
    Lista blocos parlamentares da Câmara dos Deputados.

    Returns:
        Lista de blocos partidários com membros
    """
    params = {"ordem": "ASC", "ordenarPor": "nome"}

    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint="/blocos",
        params=params
    )


def frentes_parlamentares() -> dict:
    """
    Lista frentes parlamentares da Câmara dos Deputados.

    Returns:
        Lista de frentes parlamentares com objetivos
    """
    params = {"ordem": "ASC", "ordenarPor": "titulo"}

    return _call_api(
        base_url="https://dadosabertos.camara.leg.br/api/v2",
        endpoint="/frentes",
        params=params
    )


# Mapeamento de funções disponíveis
AVAILABLE_TOOLS = {
    "buscar_senadores": buscar_senadores,
    "buscar_proposicoes_senado": buscar_proposicoes_senado,
    "detalhes_proposicao_senado": detalhes_proposicao_senado,
    "votacoes_senado": votacoes_senado,
    "listar_comissoes_senado": listar_comissoes_senado,
    "detalhes_comissao_senado": detalhes_comissao_senado,
    "membros_comissao_senado": membros_comissao_senado,
    "reunioes_comissao_senado": reunioes_comissao_senado,
    "buscar_agenda_comissao": buscar_agenda_comissao,
    "detalhes_reuniao_comissao": detalhes_reuniao_comissao,
    "videos_reuniao_comissao": videos_reuniao_comissao,
    "agenda_senado": agenda_senado,
    "materia_senado": materia_senado,
    "autorias_senador": autorias_senador,
    "listar_partidos_senado": listar_partidos_senado,
    "listar_tipos_cargo_comissoes": listar_tipos_cargo_comissoes,
    "mesa_diretora_congresso_nacional": mesa_diretora_congresso_nacional,
    "mesa_diretora_senado_federal": mesa_diretora_senado_federal,
    "buscar_deputados": buscar_deputados,
    "detalhes_deputado": detalhes_deputado,
    "buscar_proposicoes_camara": buscar_proposicoes_camara,
    "detalhes_proposicao_camara": detalhes_proposicao_camara,
    "votacoes_camara": votacoes_camara,
    "despesas_deputado": despesas_deputado,
    "eventos_camara": eventos_camara,
    "listar_orgaos_camara": listar_orgaos_camara,
    "detalhes_orgao_camara": detalhes_orgao_camara,
    "membros_orgao_camara": membros_orgao_camara,
    "partidos_camara": partidos_camara,
    "blocos_camara": blocos_camara,
    "frentes_parlamentares": frentes_parlamentares,
}


# Schema das ferramentas para Gemini/Groq
TOOLS_SCHEMA = [
    {
        "name": "buscar_senadores",
        "description": "Lista senadores em exercício, opcionalmente filtrados por UF.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "uf": {
                    "type": "STRING",
                    "description": "Sigla do estado (ex: 'SP', 'RJ', 'MG') ou None para todos"
                }
            }
        }
    },
    {
        "name": "buscar_proposicoes_senado",
        "description": "Busca proposições no Senado por tipo e ano.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "sigla": {
                    "type": "STRING",
                    "description": "Tipo da proposição (ex: 'PEC', 'PL', 'PLS', 'MPV')"
                },
                "ano": {
                    "type": "STRING",
                    "description": "Ano da proposição (ex: '2024', '2025')"
                }
            },
            "required": ["sigla"]
        }
    },
    {
        "name": "detalhes_proposicao_senado",
        "description": "Obtém detalhes completos de uma proposição do Senado.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "codigo": {
                    "type": "STRING",
                    "description": "Código da proposição (ex: '132046')"
                }
            },
            "required": ["codigo"]
        }
    },
    {
        "name": "votacoes_senado",
        "description": "Lista votações do Senado em um período.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data_inicio": {
                    "type": "STRING",
                    "description": "Data inicial no formato AAAAMMDD (ex: '20250101')"
                },
                "data_fim": {
                    "type": "STRING",
                    "description": "Data final no formato AAAAMMDD (opcional)"
                }
            },
            "required": ["data_inicio"]
        }
    },
    {
        "name": "listar_comissoes_senado",
        "description": "Lista comissões do Senado Federal.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "tipo": {
                    "type": "STRING",
                    "description": "Tipo da comissão - 'permanente', 'cpi', 'temporaria', 'orgaos' (padrão: 'permanente')"
                }
            }
        }
    },
    {
        "name": "detalhes_comissao_senado",
        "description": "Obtém detalhes de uma comissão do Senado.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "codigo": {
                    "type": "STRING",
                    "description": "Código numérico da comissão (ex: '40' para CAS, '38' para CAE, '34' para CCJ)"
                }
            },
            "required": ["codigo"]
        }
    },
    {
        "name": "membros_comissao_senado",
        "description": "Lista membros de uma comissão do Senado.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "codigo": {
                    "type": "STRING",
                    "description": "Código da comissão"
                }
            },
            "required": ["codigo"]
        }
    },
    {
        "name": "reunioes_comissao_senado",
        "description": "Lista reuniões de uma comissão do Senado.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "codigo": {
                    "type": "STRING",
                    "description": "Código da comissão"
                },
                "data_inicio": {
                    "type": "STRING",
                    "description": "Data inicial no formato AAAAMMDD (opcional)"
                },
                "data_fim": {
                    "type": "STRING",
                    "description": "Data final no formato AAAAMMDD (opcional)"
                }
            },
            "required": ["codigo"]
        }
    },
    {
        "name": "buscar_agenda_comissao",
        "description": "Busca a agenda de comissões do Senado em um período para encontrar códigos de reuniões.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data_inicio": {
                    "type": "STRING",
                    "description": "Data inicial no formato YYYYMMDD (ex: '20251209')"
                },
                "data_fim": {
                    "type": "STRING",
                    "description": "Data final no formato YYYYMMDD (opcional)"
                }
            },
            "required": ["data_inicio"]
        }
    },
    {
        "name": "detalhes_reuniao_comissao",
        "description": "Obtém detalhes completos de uma reunião específica de comissão.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "codigo_reuniao": {
                    "type": "STRING",
                    "description": "Código da reunião obtido via buscar_agenda_comissao"
                }
            },
            "required": ["codigo_reuniao"]
        }
    },
    {
        "name": "videos_reuniao_comissao",
        "description": "Obtém os vídeos de uma reunião específica de comissão.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "codigo_reuniao": {
                    "type": "STRING",
                    "description": "Código da reunião"
                }
            },
            "required": ["codigo_reuniao"]
        }
    },
    {
        "name": "agenda_senado",
        "description": "Obtém a agenda geral do Senado Federal (sessões plenárias).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "data": {
                    "type": "STRING",
                    "description": "Data no formato AAAAMMDD (ex: '20250123'). Se omitido, retorna agenda atual."
                }
            }
        }
    },
    {
        "name": "materia_senado",
        "description": "Obtém informações completas sobre uma matéria legislativa do Senado.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "codigo": {
                    "type": "STRING",
                    "description": "Código da matéria (ex: '132046')"
                }
            },
            "required": ["codigo"]
        }
    },
    {
        "name": "autorias_senador",
        "description": "Lista proposições de autoria de um senador.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "codigo_senador": {
                    "type": "STRING",
                    "description": "Código do senador"
                }
            },
            "required": ["codigo_senador"]
        }
    },
    {
        "name": "listar_partidos_senado",
        "description": "Obtém a lista dos Partidos Políticos em atividade e/ou extintos no Senado Federal.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "listar_tipos_cargo_comissoes",
        "description": "Obtém a lista de Tipos de Cargo nas Comissões do Senado Federal e Congresso Nacional.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "mesa_diretora_congresso_nacional",
        "description": "Obtém a Composição dos integrantes da Mesa Diretora do Congresso Nacional.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "mesa_diretora_senado_federal",
        "description": "Obtém a Composição dos integrantes da Mesa Diretora do Senado Federal.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "buscar_deputados",
        "description": "Lista deputados em exercício, com filtros opcionais.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "siglaUf": {
                    "type": "STRING",
                    "description": "Sigla do estado (ex: 'SP', 'RJ')"
                },
                "siglaPartido": {
                    "type": "STRING",
                    "description": "Sigla do partido (ex: 'PT', 'PL', 'PSDB')"
                }
            }
        }
    },
    {
        "name": "detalhes_deputado",
        "description": "Obtém informações detalhadas de um deputado.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "id_deputado": {
                    "type": "STRING",
                    "description": "ID do deputado"
                }
            },
            "required": ["id_deputado"]
        }
    },
    {
        "name": "buscar_proposicoes_camara",
        "description": "Busca proposições na Câmara dos Deputados.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "siglaTipo": {
                    "type": "STRING",
                    "description": "Tipo da proposição (ex: 'PL', 'PEC', 'MPV')"
                },
                "ano": {
                    "type": "STRING",
                    "description": "Ano da proposição (ex: '2024')"
                },
                "autor": {
                    "type": "STRING",
                    "description": "Nome ou ID do autor"
                },
                "keywords": {
                    "type": "STRING",
                    "description": "Palavras-chave para busca"
                }
            }
        }
    },
    {
        "name": "detalhes_proposicao_camara",
        "description": "Obtém detalhes completos de uma proposição da Câmara.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "id_proposicao": {
                    "type": "STRING",
                    "description": "ID da proposição"
                }
            },
            "required": ["id_proposicao"]
        }
    },
    {
        "name": "votacoes_camara",
        "description": "Lista votações da Câmara dos Deputados.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "id_proposicao": {
                    "type": "STRING",
                    "description": "ID da proposição (opcional)"
                },
                "dataInicio": {
                    "type": "STRING",
                    "description": "Data inicial no formato AAAA-MM-DD"
                },
                "dataFim": {
                    "type": "STRING",
                    "description": "Data final no formato AAAA-MM-DD"
                }
            }
        }
    },
    {
        "name": "despesas_deputado",
        "description": "Obtém despesas da cota parlamentar de um deputado.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "id_deputado": {
                    "type": "STRING",
                    "description": "ID do deputado"
                },
                "ano": {
                    "type": "STRING",
                    "description": "Ano das despesas (ex: '2024')"
                },
                "mes": {
                    "type": "STRING",
                    "description": "Mês das despesas (1-12, opcional)"
                }
            },
            "required": ["id_deputado", "ano"]
        }
    },
    {
        "name": "eventos_camara",
        "description": "Lista eventos (reuniões, audiências) da Câmara.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "dataInicio": {
                    "type": "STRING",
                    "description": "Data inicial no formato AAAA-MM-DD"
                },
                "dataFim": {
                    "type": "STRING",
                    "description": "Data final no formato AAAA-MM-DD"
                }
            }
        }
    },
    {
        "name": "listar_orgaos_camara",
        "description": "Lista todos os órgãos (comissões, frentes, etc) da Câmara.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "detalhes_orgao_camara",
        "description": "Obtém detalhes de um órgão (comissão) da Câmara.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "id_orgao": {
                    "type": "STRING",
                    "description": "ID do órgão"
                }
            },
            "required": ["id_orgao"]
        }
    },
    {
        "name": "membros_orgao_camara",
        "description": "Lista membros de um órgão (comissão) da Câmara.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "id_orgao": {
                    "type": "STRING",
                    "description": "ID do órgão"
                }
            },
            "required": ["id_orgao"]
        }
    },
    {
        "name": "partidos_camara",
        "description": "Lista partidos com representação na Câmara dos Deputados.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "blocos_camara",
        "description": "Lista blocos parlamentares da Câmara dos Deputados.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "frentes_parlamentares",
        "description": "Lista frentes parlamentares da Câmara dos Deputados.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    }
]
