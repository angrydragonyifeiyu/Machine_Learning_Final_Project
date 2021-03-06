from __future__ import absolute_import, division, print_function, unicode_literals

# Import libraries
import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.utils import plot_model
import matplotlib.pyplot as plt
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import scale
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from sklearn.linear_model import LogisticRegression

# Configure the programme
plt.style.use('seaborn-dark-palette')

# Specify global parameters
input_path = 'Customer Churn with ANN/'
input_file = 'Telco-Customer-Churn.csv'
output_path = '/output/'
output_file = 'output.csv'
categorical_columns = ['gender', 'seniorcitizen', 'partner', 'dependents', 'tenure', 'phoneservice', 'multiplelines', 'internetservice', 'onlinesecurity', 'onlinebackup', 'deviceprotection', 'techsupport', 'streamingtv', 'streamingmovies', 'contract', 'paperlessbilling', 'paymentmethod', 'churn']

class Solver:
	'''Executes sub-modules through this class object'''	
	def __init__(self, input_path, input_file, output_path, output_file, impute_nan = False, test_size = 0.2, dropout_rate = 0.2):
		'''Loads global variables into the object'''
		Aux.directory_create(input_path + output_path[1:-1]) # Create a directory for output files if not exist
		self.input_path = input_path
		self.input_file = input_file
		self.output_path = output_path
		self.output_file = output_file
		self.impute_nan = impute_nan # Control methods to handle missing values
		self.test_size = test_size
		self.dropout_rate = dropout_rate
		self.df = pd.read_csv(self.input_path + self.input_file) # Import data
		self.X_train = pd.DataFrame()
		self.X_test = pd.DataFrame()
		self.y_train = pd.DataFrame()
		self.y_test = pd.DataFrame()
		self.model = None
		self.predicted = pd.Series()

	def data_clean(self):
		'''Cleans the data'''
		self.df = Aux.column_names_clean(self.df) # Eliminate space and upper case characters in column names
		self.df.drop(['customerid'], axis = 1, inplace = True) # Drop uniquely identifiable column
		self.df['totalcharges'].replace(' ', np.nan, inplace = True) # Standardise missing value representations
		self.df['totalcharges'] = self.df['totalcharges'].astype(float) # Specify continuous column
		if self.impute_nan:
			self.df['totalcharges'].fillna(self.df['totalcharges'].mean(), inplace = True) # Impute missing data by replacing them with column means
		else:
			self.df.dropna(subset = ['totalcharges'], inplace = True)
		self.df[categorical_columns] = self.df[categorical_columns].astype('category') # Specify discrete columns
		self.df['totalcharges'] = self.df['totalcharges'].astype(float)
		self.df['totalcharges'] = np.log(self.df['totalcharges']) # Log transform target feature
		self.df = pd.concat([pd.get_dummies(self.df.drop('churn', axis = 1)), self.df['churn']], axis = 1) # Enable one-hot enconding
		self.df['churn'].replace({'Yes': 1, 'No': 0}, inplace = True) # Standardise binary variable representation
		self.df = Aux.column_names_clean(self.df) # Eliminate space and upper case characters in column names
		self.X_train, self.X_test, self.y_train, self.y_test = Aux.data_partition(self.df.drop('churn', axis = 1), self.df['churn'], test_size = self.test_size) # Split data into different sets
		self.X_train, self.X_test = pd.DataFrame(scale(self.X_train), columns = self.df.columns[:-1]), pd.DataFrame(scale(self.X_test), columns = self.df.columns[:-1]) # Normalise data

	def model_define(self):
		'''Defines the architecture for churn rate prediction with a neural network model'''
		inputs = keras.Input(shape = (self.df.shape[1] - 1,), name = 'churn_data')
		x = layers.Dense(16, activation = 'relu', name = 'hidden_1')(inputs)
		x = layers.Dropout(rate = self.dropout_rate, name = 'dropout_1')(x)
		x = layers.Dense(16, activation = 'relu', name = 'hidden_2')(x)
		x = layers.Dropout(rate = self.dropout_rate, name = 'dropout_2')(x)
		x = layers.Dense(8, activation = 'relu', name = 'hidden_3')(x)
		x = layers.Dropout(rate = self.dropout_rate, name = 'dropout_3')(x)
		outputs = layers.Dense(1, activation = 'sigmoid', name = 'classification')(x)
		self.model = keras.Model(inputs = inputs, outputs = outputs, name = 'customer_churn_model')
		self.model.summary()
		plot_model(self.model, to_file = self.input_path + self.output_path + 'computational_graph.png', show_shapes = True, dpi = 300)

	def model_train(self):
		'''Trains the model with historical churn data'''
		self.model.compile(loss = keras.losses.BinaryCrossentropy(),
			      optimizer = keras.optimizers.Adam(),
			      metrics = ['accuracy'])
		history = self.model.fit(self.X_train, self.y_train,
				    batch_size = 64,
				    epochs = 10,
				    validation_split = 0.2)
		Aux.train_history_vis(history.history, path = self.input_path + self.output_path) # Visualises training history

	def model_predict(self):
		'''Predicts values with new data given a previously trained model'''
		self.predicted = self.model.predict(self.X_test) # Predict target feature for test data
	
	def model_evaluate(self):
		'''Evaluates model based on test data'''
		# Accuracy measure
		test_scores = self.model.evaluate(self.X_test, self.y_test, verbose = 2) # Evaluate performance based on cross-entropy and classification accuracy
		self.model.save(self.input_path + self.output_path + 'model')
		print('Test loss:', test_scores[0])
		print('Test accuracy:', test_scores[1])

		# AUC measure
		roc_auc = roc_auc_score(self.y_test, self.predicted) # Evaluate performance based on AUC
		print('AUC score:', roc_auc)

		# Precision, recall and F1 measures
		predicted_class = np.where(self.predicted <= 0.5, 0, 1)
		p_r_f1 = precision_recall_fscore_support(self.y_test, predicted_class) # Evalute performance based on F1 measures
		print(p_r_f1)

	def exec(self):
		self.data_clean()
		self.model_define()
		self.model_train()
		self.model_predict()
		self.model_evaluate()

class Logit:
	'''An alternative classifier to neural networks'''
	def logit(X_train, y_train, X_test, y_test):
		'''Runs logistic regression on train data'''
		logit_obj  = LogisticRegression(random_state = 42).fit(X_train, y_train)
		pred_class = logit_obj.predict(X_test)
		print('The accuracy of classification by logistic regression is ' + str(logit_obj.score(X_test, y_test)))

class Aux:
	'''Supports the main solver module'''
	def column_names_clean(df):
		'''Cleans column names'''
		df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
		return df

	def directory_create(path):
		'''Creates a directory if not already exists'''
		if not os.path.exists(path):
			os.makedirs(path)	

	def data_partition(X, y, test_size):
		'''Splits data into training and testing sets'''
		X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = test_size, random_state = 42)
		return X_train, X_test, y_train, y_test

	def train_history_vis(history, path):
		'''Visualises the model's training history in terms of loss and accuracy'''
		# Plot training & validation accuracy values
		plt.figure(figsize = (16,9))
		plt.plot(history['accuracy'])
		plt.plot(history['val_accuracy'])
		plt.title('Model Accuracy')
		plt.ylabel('Accuracy')
		plt.xlabel('Epoch')
		plt.legend(['Train', 'Test'], loc = 'upper left')
		plt.savefig(path + 'Accuracy_History.png', dpi = 300)
		plt.close()

		# Plot training & validation loss values
		plt.figure(figsize = (16,9))
		plt.plot(history['loss'])
		plt.plot(history['val_loss'])
		plt.title('Model Loss')
		plt.ylabel('Loss')
		plt.xlabel('Epoch')
		plt.legend(['Test', 'Train'], loc = 'upper left')
		plt.savefig(path + 'Loss History.png', dpi = 300)
		plt.close()

def main():
	solver_object = Solver(input_path, input_file, output_path, output_file, impute_nan = True)
	solver_object.exec()

	Logit.logit(solver_object.X_train, solver_object.y_train, solver_object.X_test, solver_object.y_test)

if __name__ == '__main__':
	main()
