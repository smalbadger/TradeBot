import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

# Please Overwrite data of vals1 and vals2 for finishing the graph, I don't have the data yet.
vals1 = [1, 2, 3, 4]
vals2 = [1, 2, 3, 4]
fig, ax = plt.subplots()
labels = 'CoinA', 'CoinB', 'CoinC', 'CoinD', 'InnerA', 'InnerB', 'InnerC', 'InnerD'
ax.pie(vals1, radius=1.0,autopct='%1.1f%%',pctdistance=0.9)
ax.pie(vals2, radius=0.5,autopct='%1.2f%%',pctdistance=0.5)
ax.set(aspect="equal", title='User Balance')
#plt.legend()
plt.legend(labels,bbox_to_anchor=(1.05, 1), loc='best', borderaxespad=0.)
plt.show()


