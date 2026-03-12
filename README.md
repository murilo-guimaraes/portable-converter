# Portable Converter Master - v12.6

> Esse README.md é temporário.

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pillow](https://img.shields.io/badge/Pillow-101010?style=for-the-badge&logo=pypi&logoColor=white)](https://python-pillow.org/)
[![Tkinter](https://img.shields.io/badge/Tkinter-00599C?style=for-the-badge&logo=python&logoColor=white)](https://docs.python.org/3/library/tkinter.html)

Aplicação desktop desenvolvida em Python para conversão em lote de imagens, utilizando uma interface dinâmica baseada em Canvas para gerenciamento visual da fila de arquivos através do sistema **Flash Cover Flow**.

## Visualizar Projeto
O repositório oficial e o código-fonte estão disponíveis em:  
**[github.com/murilo-guimaraes/portable-converter](https://github.com/murilo-guimaraes/portable-converter)**

> **Nota:** Interface e lógica de processamento em constante evolução para garantir compatibilidade e performance. Feedbacks e pull requests são bem-vindos.

---

## O que há de novo?
### Versão v12.6
Refinamento de interface e novas funcionalidades de fluxo de trabalho.

* **Escala Progressiva**: Ajuste dinâmico de dimensões nas extremidades do carrossel para evitar o corte de frames no Canvas.
* **Gestão de Saída**: Implementação de Checkbox para definição opcional de criação da pasta "Convertidos".
* **Automação de Sistema**: Opção para abertura automática do Windows Explorer no diretório de destino após a conclusão do processo.
* **Estabilidade**: Correção de exceções de atributo e otimização de memória no carregamento de previews dinâmicos.

---

## Funcionalidades e Tecnologias
* **Flash Cover Flow**: Sistema de carrossel com profundidade visual, brilho dinâmico e renderização em tempo real via PIL (Pillow).
* **Drag and Drop**: Suporte nativo para importação de arquivos via arraste diretamente para a interface (TkinterDnD2).
* **Fila Avançada**: Janela de gerenciamento secundária com suporte a atalhos de teclado (`Delete`/`Backspace`) e visualização detalhada.
* **Suporte Multi-Formato**: Conversão compatível com PNG, ICO, JPG, WEBP, JPEG, BMP, GIF e TIFF.

---

## Estrutura de Arquivos
```text
├── assets/                 # Recursos visuais, ícones e screenshots
├── conversor.py            # Script principal (Lógica de processamento e GUI)
├── README.md               # Documentação técnica do projeto
└── Convertidos/            # Diretório de saída gerado automaticamente (opcional)
```
## Instalação e Execução

1. Instale as dependências via gerenciador de pacotes:

    `pip install Pillow tkinterdnd2`

2. Execute o script principal:
 
    `python conversor.py`
