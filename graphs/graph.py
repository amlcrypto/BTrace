import datetime
from matplotlib import patches
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from graphs.my_view import my_draw_networkx_edge_labels
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

            df = pd.DataFrame.from_dict(tr_to_pandas)
            df = df.sort_values(by=['date'])
            df_token = pd.DataFrame(df.filter(['token'], axis=1))
            df  = pd.DataFrame(df.filter(['wallet','dest','sum'], axis=1))

            nodes = df.values.tolist()
            nodes_crop = []
            for node in nodes:
                nodes_crop.append((node[0], node[1]))

            G = nx.MultiDiGraph()

            for node in nodes:
                G.add_edge(node[0], node[1], weight=node[2])

            arrSt1 = patches.ArrowStyle.CurveFilledB(head_length=1,head_width=0.5 )

            labels = nx.get_edge_attributes(G,'weight')

            # for key in lables.keys():
            labels_new = {} # {('addr_1',addr_2): [in, out]} where in, out - numbers
            old_labels = list(labels.keys())

            for key in old_labels:
                if (key[0], key[1]) in labels_new:
                    labels_new[(key[0], key[1])] = labels_new[(key[0], key[1])]+ labels[key]
                    continue
                else:
                    labels_new[(key[0], key[1])] = labels[key]
                    continue

            G1 = nx.DiGraph()

            for label in labels_new.keys():
                G1.add_edge(label[0], label[1], weight=labels_new[label])

            pos=nx.shell_layout(G1)


            # for key in labels.keys(): #zip(labels.keys(), df_token.iterrows()):
            #     labels[key] = str(labels[key]) #+' '+ str(token[1].token)
            nodes_crop.reverse()
            temp = []
            for x in nodes_crop:
                if x not in temp:
                    temp.append(x)
            nodes_crop = temp

            nd_colors = ['green']*len(G1.nodes())
            i = 0
            for node in pos.keys():
                LOGGER.info(f'{node}-{nodes_crop[0][1]}')
                if node == nodes_crop[0][1]:
                    nd_colors[i] = 'red'
                    break
                else:
                    i += 1

            edge_colors = ['green'] * len(G1.edges())
            i = 0
            for edge in G1.edges():
                if edge == nodes_crop[0]:
                    edge_colors[i] = 'red'
                    break
                else:
                    i += 1

            curved_edges_colors = []
            straight_edges_colors = []

            edges_for_find_color = list(G1.edges())[:]
            curved_edges = [edge for edge in G1.edges() if reversed(edge) in G1.edges()]
            i = 0
            curv_index = []
            for curved_edge in curved_edges:
                curved_edges_colors.append(edge_colors[edges_for_find_color.index(curved_edge)])
                curv_index.append(edges_for_find_color.index(curved_edge))

            for i in range(0, len(edge_colors)):
                if i in curv_index:
                    continue
                else:
                    straight_edges_colors.append(edge_colors[i])

            plt.style.use('mpl20')
            plt.figure(figsize=(20,14), dpi=50)
            plt.axis('off')


            G = G1
            #pos=nx.shell_layout(G)
            nx.draw_networkx_nodes(G, pos, node_color=nd_colors, node_size= 500)
            nx.draw_networkx_labels(G, pos, clip_on=False,  horizontalalignment= 'left')
            curved_edges = [edge for edge in G.edges() if reversed(edge) in G.edges()]

            if len(curved_edges) == 0:
                straight_edges = list(G.edges())[:]
            else:
                straight_edges = list(set(G.edges()) - set(curved_edges))

            nx.draw_networkx_edges(G, pos,edgelist=straight_edges, arrowstyle=arrSt1, edge_color=straight_edges_colors)
            arc_rad = 0.15
            nx.draw_networkx_edges(G, pos,edgelist=curved_edges, connectionstyle=f'arc3, rad = {arc_rad}', arrowstyle=arrSt1, edge_color=curved_edges_colors)

            edge_weights = nx.get_edge_attributes(G,'weight')
            curved_edge_labels = {edge: edge_weights[edge] for edge in curved_edges}
            straight_edge_labels = {edge: edge_weights[edge] for edge in straight_edges}

            my_draw_networkx_edge_labels(G, pos, edge_labels=curved_edge_labels, rotate=False,rad = arc_rad, font_size=20)
            nx.draw_networkx_edge_labels(G, pos, edge_labels=straight_edge_labels, rotate=False, font_size=20)
            now = datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
            plt.savefig(f'{PATH}/graphs/img/{user_id}-{date_last_transactions}-{now}.jpg', dpi=250, bbox_inches='tight')

            return now
        except Exception as e:
            LOGGER.error(str(e))

