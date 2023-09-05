import ssl

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
import yaml

from datetime import datetime
from pathlib import Path

from config import config


class TLSAdapter(requests.adapters.HTTPAdapter):
    
    def init_poolmanager(self, *args, **kwargs):
        
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        ctx.options |= 0x4   # <-- the key part here, OP_LEGACY_SERVER_CONNECT
        kwargs["ssl_context"] = ctx
        
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)

def gerar_periodos():

    data_hoje = datetime.now()
    p = [f'{data_hoje.year}{data_hoje.month-offset:02d}' for offset in range(1, 7)]
    periodos = "|".join(p)
        
    return periodos

def gerar_url(periodos):
    
    url = f"""https://servicodados.ibge.gov.br/api/v3/agregados/7063/
    periodos/{periodos}/variaveis/44?localidades=N1[all]&classificacao=
    315[7169]""".replace('\n', '').replace('    ', '')
    
    return url

def processar_dados(dados_brutos):
    
    serie=dados_brutos[0]['resultados'][0]['series'][0]['serie']
    dados_processados = {
        'data': [formatar_texto(texto) for texto in serie.keys()], 
        'INPC': [float(valor) for valor in serie.values()]
    }
    dados_processados = pd.DataFrame(data=dados_processados)
    dados_processados = dados_processados.sort_values(
        by='data', ascending=True
    )
    
    return dados_processados

def formatar_texto(periodo):
    
    r = f'{periodo[4:6]}-{periodo[0:4]}'
    
    return r

def montar_sessao():
    
    sessao = requests.Session()
    sessao.mount("https://", TLSAdapter())
    
    return sessao

def definir_tema():
    
    with open(config.CONFIG_DIR / 'plotting_parameters.yaml') as f:
        plotting_parameters = yaml.safe_load(f)
        sns.set_theme(**plotting_parameters)
        
    return None
    
def configurar_plotagem(ax):
    
    ax.set_title('Índice Nacional de Preços ao Consumidor dos últimos 6 meses')
    ax.set_xlabel('Mês')
    ax.set_ylabel('INPC (%)')
    
    return None

def gerar_plotagem(dados_processados):
    
    definir_tema()
    fig, ax = plt.subplots(figsize=(15, 5))
    configurar_plotagem(ax)
    sns.lineplot(data=dados_processados, 
            x='data',
            y='INPC',
            ax=ax)
    
    return fig

def salvar_fig(fig, periodos):
    
    fig.savefig(config.ARTEFATOS_DIR / periodos)
    
    return None


if __name__ == '__main__':
    periodos = gerar_periodos()
    url = gerar_url(periodos)
    sessao = montar_sessao()
    dados_brutos = sessao.get(url=url).json()
    dados_processados = processar_dados(dados_brutos)
    fig = gerar_plotagem(dados_processados)
    salvar_fig(fig, periodos)