<img width="1636" height="374" alt="image" src="https://github.com/user-attachments/assets/82f48ea1-1dd4-4b23-8ce4-0df75d3dc969" />

# CRAM to Binxelview Converter

Conversor de dumps CRAM do Mega Drive / Genesis para paletas `.pal` RGB24 compatíveis com o Binxelview.

## Recursos

- Entrada por caminho digitado ou seleção de arquivo.
- Campo de saída editável, com botão para escolher o destino.
- Arrastar e soltar (opcional, requer `tkinterdnd2`).
- Dumps CRAM de 16 cores (32 bytes) e 256 cores (512 bytes).
- Escolha da ordem dos bytes (`big` ou `little`).
- Exportação RGB24 sem cabeçalho.
- Reordenação de índices por inversão de bits, conforme a organização implementada nesta versão.

> Nota: a regra de reordenação é aplicada aos índices: para 16 cores, 0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15. Para 256 cores, a mesma operação é aplicada a 8 bits. Confirme o mapeamento com uma paleta de referência do seu fluxo Binxelview.

## Requisitos

- Python 3.9 ou superior
- Tkinter (normalmente incluído na instalação oficial do Python)
- Opcional: `tkinterdnd2` para arrastar e soltar

## Instalação

```bash
python -m pip install -r requirements.txt
```

Para usar sem drag-and-drop, não é necessário instalar dependências externas.

## Executar

```bash
python src/cram2binxel_md.py
```

1. Informe o arquivo CRAM no campo **Input** ou use **Browse…**.
2. Informe o caminho `.pal` no campo **Output** ou use **Save as…**.
3. Selecione a ordem dos bytes apropriada ao dump.
4. Clique em **Convert**.
5. No Binxelview, carregue o `.pal` pela opção de carregar paleta.

## Formato esperado

| Cores | Tamanho do CRAM | Tamanho da saída RGB24 |
|---:|---:|---:|
| 16 | 32 bytes | 48 bytes |
| 256 | 512 bytes | 768 bytes |

O arquivo de saída contém apenas triplas RGB (`R`, `G`, `B`), sem cabeçalho.

## Estrutura

```text
cram2binxel_MD/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
└── src/
    └── cram2binxel_md.py
```

## Limitações

Este programa converte dumps CRAM brutos; não extrai automaticamente CRAM de ROMs. A opção de ordem dos bytes altera a leitura das palavras de 16 bits, não a sequência de canais RGB.
