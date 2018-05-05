import csv
import numpy as np
from math import exp, sqrt
from pandas import read_csv, to_numeric, concat, DataFrame
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from sklearn import preprocessing
from sklearn.metrics import mean_squared_error
from numpy import concatenate

import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense, LSTM

from simulation import TradingSimulation

from numpy.random import seed
from tensorflow import set_random_seed
#seed(2)
#set_random_seed(2)


##############################################################
############ read in csv file and convert types ##############
##############################################################
print("Reading CSV file...", end='')
docs = []
with open("01-Jan-2018_16-Apr-2018.csv", "r") as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		row['time'] = datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S')
		row['price'] = float(row['price'])
		docs.append(row)
print("\t\tDONE")

##############################################################
## take price averages and record valuable data in a window ##
##############################################################
print("Preprocessing data...", end='')
processed_docs = []
time_delta = timedelta(minutes = 3)
start_time = docs[0]["time"]
avg_price = 0
count = 0
numSells = 0
numBuys = 0
prices = []
for doc in docs:
	if (doc["time"] - start_time) < time_delta:
		count += 1
		prices.append(doc["price"])
		avg_price += float(doc["price"])
		if doc['side'] == 'buy':
			numBuys+=1
		elif doc['side'] == 'sell':
			numSells+=1
		
	else:
		#tie up current average
		avg_price /= count
		window = {}
		window['standard_deviation'] = np.std(np.asarray(prices))
		window['price'] = avg_price
		window['time']  = start_time + time_delta
		window['buys']  = numBuys
		window['sells'] = numSells
		processed_docs.append(window)
		
		#start new average
		prices = []
		start_time = doc["time"]
		prices.append(doc['price'])
		avg_price = float(doc["price"])
		count = 1
		numBuys = 0
		numSells = 0
		if doc['side'] == 'buy':
			numBuys+=1
		elif doc['side'] == 'sell':
			numSells+=1
print("\t\tDONE")

##############################################################
######################### Label Data #########################
##############################################################
print("Labeling data...", end='')
time_delta = timedelta(hours = 3)
for i in range(len(processed_docs)):
	start_time = processed_docs[i]["time"]
	end_time   = start_time + time_delta
	score      = 0
	j=i
	while(j<len(processed_docs) and processed_docs[j]['time'] < end_time):
		score += (processed_docs[j]["price"] - processed_docs[i]["price"]) * 0.5 * exp(i-j)
		j+=1
	processed_docs[i]["score"] = score
	
print("\t\tDONE")
			
##############################################################
############### plot the buys and sells for fun ##############
##############################################################
'''
print("Printing data...", end='')
i=1
plt.figure()

# comment out any fields that you don't want to see for better picutres.
groups = ["price","score"]#,"standard_deviation","buys","sells"]
for group in groups:
	plt.subplot(len(groups), 1, i)
	plt.plot([data['time'] for data in processed_docs],
		[data[group] for data in processed_docs])
	plt.title(group, y=0.5, loc='right')
	i += 1
plt.show()
print("\t\tDONE")
'''

##############################################################
######### write the processed data to a new csv file #########
##############################################################
print("Writing CSV file...", end='')
fieldNames = sorted(list(processed_docs[0].keys()))
fieldNames.pop(fieldNames.index('score'))
fieldNames.append('score')
fieldNames.pop(fieldNames.index('time'))
fieldNames.insert(0,'time')
with open('preprocessed_data.csv','w') as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames = fieldNames)
	writer.writeheader()
	
	for doc in processed_docs:
		doc['time'] = doc['time'].strftime('%Y-%m-%d %H:%M:%S')
		writer.writerow(doc)
print("\t\tDONE")

##############################################################
################### More Data Preprocessing ##################
##############################################################
print("More Preprocessing Data...", end='')
dataset = read_csv('preprocessed_data.csv', header=0)
dataset.columns = fieldNames
#dataset.index.name = 'time'
# drop the first 24 hours
dataset = dataset[24:]
# save to file
dataset.to_csv('processed_data.csv')
print("\tDONE")

##############################################################
################### Getting Ready To Learn ###################
##############################################################
# convert series to supervised learning problem
print("Convert to Supervised Learning..", end='')
def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
	n_vars = 1 if type(data) is list else data.shape[1]
	df = data
	cols, names = list(), list()
	# input sequence (t-n, ... t-1)
	for i in range(n_in, 0, -1):
		cols.append(df.shift(i))
		names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
	# forecast sequence (t, t+1, ... t+n)
	for i in range(0, n_out):
		cols.append(df.shift(-i))
		if i == 0:
			names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
		else:
			names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
	# put it all together
	agg = concat(cols, axis=1)
	agg.columns = names
	# drop rows with NaN values
	if dropnan:
		agg.dropna(inplace=True)
	return agg
 
# load dataset
dataset = read_csv('processed_data.csv', header=0)
float_cols = ["price","score","standard_deviation","buys","sells"]
for col in float_cols:
	dataset[col] = to_numeric(dataset[col])

# normalize features
scale_cols1 = ["buys", "sells", "price", "standard_deviation"]
scale_cols2 = ["score"]
scaler1 = preprocessing.MinMaxScaler(feature_range=(0, 1))
scaler2 = preprocessing.MinMaxScaler(feature_range=(-1, 1))

# scale the columns - uncomment to scale
#dataset[scale_cols1] = scaler1.fit_transform(dataset[scale_cols1])
#dataset[scale_cols2] = scaler2.fit_transform(dataset[scale_cols2])

# frame as supervised learning
reframed = series_to_supervised(dataset, 1, 1)
# drop columns we don't want to predict
reframed.drop(reframed.columns[[7,8,9,10,11,12,13]], axis=1, inplace=True)
#print(reframed.head())
#print(dataset.head())
print("DONE")

##############################################################
############### Prepare Train and Test Data Sets #############
##############################################################
PERCENT_TRAIN = 95
values = reframed.values
n_train = int(round(reframed.shape[0] * (PERCENT_TRAIN/100)))
train = values[:n_train, :]
test  = values[n_train:, :]
#print(test)

#split into inputs and outputs
train_X, train_y = train[:, 2:-1], train[:, -1]
test_X, test_y = test[:, 2:-1], test[:, -1]
# reshape input to be 3D [samples, timesteps, features]
train_X = train_X.reshape((train_X.shape[0], 1, train_X.shape[1]))
test_X = test_X.reshape((test_X.shape[0], 1, test_X.shape[1]))
#print(train_X.shape, train_y.shape, test_X.shape, test_y.shape)

##############################################################
###################### Make the LSTM Model ###################
##############################################################
model = Sequential()
model.add(LSTM(50, input_shape=(train_X.shape[1], train_X.shape[2])))
model.add(Dense(1))
model.compile(loss='mean_squared_logarithmic_error', optimizer='adam', metrics=['accuracy'])
# fit network
history = model.fit(train_X, train_y, epochs=10, batch_size=500, validation_data=(test_X, test_y), verbose=2, shuffle=False)

# plot history - This allows us to see how many epics we should use
'''
plt.plot(history.history['loss'], label='train')
plt.plot(history.history['val_loss'], label='test')
plt.legend()
plt.show()
'''

##############################################################
##################### Use Model to Predict ###################
##############################################################
predicted_scores = model.predict(test_X)
orig_scores = test_y
prices = test[:,3]

predicted_scores = scaler2.fit_transform(predicted_scores)
orig_scores = scaler2.fit_transform(np.reshape(test_y,(-1,1)))
prices_scaled = scaler2.fit_transform(np.reshape(prices,(-1,1)))

mean = np.mean(predicted_scores)
#print(yhat)
for i in range(len(predicted_scores)):
	predicted_scores[i] = predicted_scores[i] - mean

times = test[:,1]
for i in range(len(times)):
	times[i] = datetime.strptime(times[i], '%Y-%m-%d %H:%M:%S')
plt.plot(times,predicted_scores)
plt.plot(times,orig_scores)
plt.plot(times,prices_scaled)
plt.show()
	
##############################################################
############# Simulate Trading Given Predictions #############
##############################################################
sim = TradingSimulation(predicted_scores, prices, times)
sim.play()

	




