import datetime
from matplotlib import patches
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from logger import LOGGER

from handlers.database_handlers import TransactionHandler
from database.models import Transaction
import time

from config import PATH

class Graph():

    def __init__(self):
        pass

    def draw_graph(self, wallet, user_id ,date_user_created, date_last_transactions):
        try:
            #limit 200 tr -> drop old transaction
            tr_handler = TransactionHandler()
            transactions: list(Transaction) = tr_handler.get_transaction(wallet, date_user_created)
            if len(transactions) > 200:
                transactions = transactions [-200:]

            tr_to_pandas = {"wallet":[], "dest":[], "sum": [], "date": [], "token":[]}

            for tr in transactions:
                if time.mktime(tr.date.timetuple()) < time.mktime(date_user_created.timetuple()) \
                    and time.mktime(tr.date.timetuple()) > date_last_transactions:
                        continue
                tr_to_pandas['wallet'].append(tr.wallet_1)
                tr_to_pandas['dest'].append(tr.wallet_2)
                tr_to_pandas['sum'].append(tr.balance)
                tr_to_pandas['date'].append(time.mktime(tr.date.timetuple()))
                tr_to_pandas['token'].append(tr.token)

            plt.style.use('dark_background')
            df = pd.DataFrame.from_dict(tr_to_pandas)
            df = df.sort_values(by=['date'])
            df_token = pd.DataFrame(df.filter(['token'], axis=1))
            df  = pd.DataFrame(df.filter(['wallet','dest','sum'], axis=1))

            nodes = df.values.tolist()
            nodes_crop = []
            for node in nodes:
                nodes_crop.append([node[0], node[1]])

            G = nx.MultiDiGraph()

            for node in nodes:
                G.add_edge(node[0], node[1], weight=node[2])

            pos=nx.shell_layout(G)

            plt.figure(figsize=(9,8), dpi=18)
            plt.axis('off')

            arrSt1 = patches.ArrowStyle.CurveFilledB(head_length=0.5,head_width=0.2 )

            labels = nx.get_edge_attributes(G,'weight')
            #print(labels)
            for key, token in zip(labels.keys(), df_token.iterrows()):
                labels[key] = str(round(labels[key])) +' '+ str(token[1].token)

            nd_colors = []
            edge_colors = []
            i = 0

            for i in range(0,len(nodes)):
                if i < len(pos):
                    nd_colors.append('green')
                else:
                    pass
                if i < len(nodes) -1:
                    edge_colors.append('green')
                else:
                    edge_colors.append('red')

                if i == len(nodes)-1:
                    list_node = [(k,v) for k,v in pos.items()]
                    for j in range(0, len(list_node)):
                        if list_node[j][0] == nodes[-1][1]:
                            if j >= len(nd_colors):
                                nd_colors.append('red')
                            else:
                                nd_colors[j] = 'red'

            now = datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
            nx.draw_networkx_nodes(G, pos, node_size=50, node_color=nd_colors )
            nx.draw_networkx_edges(G, pos, edgelist=nodes_crop, edge_color=edge_colors, arrowstyle=arrSt1 )
            nx.draw_networkx_labels(G, pos, clip_on=False, font_color='w', font_size=7, horizontalalignment='left')
            #nx.draw_networkx_edge_labels(G,pos,edge_labels=labels, font_size=4, rotate=True, clip_on=False)
            plt.savefig(f'{PATH}/graphs/img/{user_id}-{date_last_transactions}-{now}.jpg', dpi=250, bbox_inches='tight')

            return now
        except Exception as e:
            LOGGER.error(str(e))

