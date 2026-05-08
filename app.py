from flask import Flask, render_template, jsonify, request
import xml.etree.ElementTree as ET
import os
import json
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

NS = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

def parse_nfe(filepath):
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()

        def find(path):
            el = root.find(path, NS)
            return el.text.strip() if el is not None and el.text else ''

        # Basic info
        nNF = find('.//nfe:nNF')
        dhEmi = find('.//nfe:dhEmi')
        natOp = find('.//nfe:natOp')

        # Emitente
        emit_nome = find('.//nfe:emit/nfe:xNome')
        emit_cnpj = find('.//nfe:emit/nfe:CNPJ')
        emit_mun = find('.//nfe:emit/nfe:enderEmit/nfe:xMun')
        emit_uf = find('.//nfe:emit/nfe:enderEmit/nfe:UF')

        # Destinatário
        dest_nome = find('.//nfe:dest/nfe:xNome')
        dest_cnpj = find('.//nfe:dest/nfe:CNPJ') or find('.//nfe:dest/nfe:CPF')
        dest_mun = find('.//nfe:dest/nfe:enderDest/nfe:xMun')
        dest_uf = find('.//nfe:dest/nfe:enderDest/nfe:UF')

        # Totais
        vNF = find('.//nfe:total/nfe:ICMSTot/nfe:vNF')
        vICMS = find('.//nfe:total/nfe:ICMSTot/nfe:vICMS')
        vST = find('.//nfe:total/nfe:ICMSTot/nfe:vST')
        vPIS = find('.//nfe:total/nfe:ICMSTot/nfe:vPIS')
        vCOFINS = find('.//nfe:total/nfe:ICMSTot/nfe:vCOFINS')
        vProd = find('.//nfe:total/nfe:ICMSTot/nfe:vProd')

        # Itens
        items = []
        for det in root.findall('.//nfe:det', NS):
            prod = det.find('nfe:prod', NS)
            if prod is not None:
                items.append({
                    'codigo': prod.findtext('nfe:cProd', '', NS),
                    'descricao': prod.findtext('nfe:xProd', '', NS),
                    'ncm': prod.findtext('nfe:NCM', '', NS),
                    'cfop': prod.findtext('nfe:CFOP', '', NS),
                    'unidade': prod.findtext('nfe:uCom', '', NS),
                    'quantidade': float(prod.findtext('nfe:qCom', '0', NS) or 0),
                    'vUnitario': float(prod.findtext('nfe:vUnCom', '0', NS) or 0),
                    'vTotal': float(prod.findtext('nfe:vProd', '0', NS) or 0),
                })

        # Chave e protocolo
        chNFe = find('.//nfe:chNFe') or find('.//nfe:infNFe').replace('NFe','') if root.find('.//nfe:infNFe', NS) is not None else ''
        infNFe = root.find('.//nfe:infNFe', NS)
        if infNFe is not None:
            chNFe = infNFe.get('Id', '').replace('NFe', '')
        nProt = find('.//nfe:nProt')
        cStat = find('.//nfe:cStat')

        # Transporte
        transp_nome = find('.//nfe:transporta/nfe:xNome')
        modFrete_map = {'0': 'Emitente', '1': 'Destinatário', '2': 'Terceiros', '9': 'Sem frete'}
        modFrete = modFrete_map.get(find('.//nfe:modFrete'), find('.//nfe:modFrete'))

        # Pagamento
        tPag_map = {'01': 'Dinheiro', '02': 'Cheque', '03': 'Cartão Crédito', '04': 'Cartão Débito', '15': 'Boleto', '99': 'Outros'}
        tPag = tPag_map.get(find('.//nfe:tPag'), find('.//nfe:tPag'))
        vPag = find('.//nfe:vPag')

        # Data formatada
        dt_emissao = None
        if dhEmi:
            try:
                dt_emissao = datetime.fromisoformat(dhEmi[:19]).strftime('%d/%m/%Y %H:%M')
            except:
                dt_emissao = dhEmi

        return {
            'arquivo': os.path.basename(filepath),
            'pasta': os.path.dirname(filepath),
            'nNF': nNF,
            'chave': chNFe,
            'dhEmi': dt_emissao,
            'dhEmi_raw': dhEmi,
            'natOp': natOp,
            'emit_nome': emit_nome,
            'emit_cnpj': emit_cnpj,
            'emit_mun': emit_mun,
            'emit_uf': emit_uf,
            'dest_nome': dest_nome,
            'dest_cnpj': dest_cnpj,
            'dest_mun': dest_mun,
            'dest_uf': dest_uf,
            'vNF': float(vNF or 0),
            'vProd': float(vProd or 0),
            'vICMS': float(vICMS or 0),
            'vST': float(vST or 0),
            'vPIS': float(vPIS or 0),
            'vCOFINS': float(vCOFINS or 0),
            'nProt': nProt,
            'cStat': cStat,
            'transp_nome': transp_nome,
            'modFrete': modFrete,
            'tPag': tPag,
            'vPag': float(vPag or 0),
            'items': items,
            'status': 'ok'
        }
    except Exception as e:
        return {
            'arquivo': os.path.basename(filepath),
            'pasta': os.path.dirname(filepath),
            'status': 'erro',
            'erro': str(e)
        }

def scan_folder(folder_path):
    results = []
    for root_dir, dirs, files in os.walk(folder_path):
        dirs.sort()
        for fname in sorted(files):
            if fname.lower().endswith('.xml'):
                full = os.path.join(root_dir, fname)
                results.append(parse_nfe(full))
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def api_scan():
    data = request.get_json()
    folder = data.get('folder', '')
    if not folder or not os.path.isdir(folder):
        return jsonify({'error': 'Pasta não encontrada'}), 400
    notas = scan_folder(folder)
    return jsonify({'notas': notas, 'total': len(notas)})

@app.route('/api/nota', methods=['POST'])
def api_nota():
    data = request.get_json()
    filepath = data.get('filepath', '')
    if not os.path.isfile(filepath):
        return jsonify({'error': 'Arquivo não encontrado'}), 400
    return jsonify(parse_nfe(filepath))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
