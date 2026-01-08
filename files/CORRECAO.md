# CORREÇÃO - 31 FERRAMENTAS + FORÇA USO DE APIS

## O QUE FOI CORRIGIDO

1. ✅ Adicionadas 6 ferramentas que faltavam (agora 31 total)
2. ✅ System prompt reforçado para FORÇAR uso das ferramentas
3. ✅ Gemini e Groq configurados para sempre chamar APIs

## FERRAMENTAS ADICIONADAS

- agenda_senado
- materia_senado
- autorias_senador
- listar_partidos_senado
- listar_tipos_cargo_comissoes
- mesa_diretora_congresso_nacional

## ARQUIVOS PARA SUBSTITUIR

### api/index.py
Sistema prompt alterado com "REGRA CRÍTICA: Você DEVE SEMPRE usar as ferramentas"

### api/senado_camara_tools.py  
31 ferramentas completas (era 25)

## TESTAR

```bash
# Verificar se as 31 ferramentas estão carregadas
curl https://seu-app.vercel.app/api/health

# Deve retornar: "tools_available": 31
```

## EXEMPLO DE PERGUNTA

"Qual o ID da reunião da CCJ do senado de 17/12/2025?"

Deve chamar: buscar_agenda_comissao(data_inicio="20251217", data_fim="20251217")
