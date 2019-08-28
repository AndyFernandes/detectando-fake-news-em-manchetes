#!/usr/bin/env python
# coding: utf-8
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import log, pi, sqrt
from scipy.stats import multivariate_normal
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import export_graphviz
from sklearn.externals.six import StringIO  
from IPython.display import Image  
from sklearn import datasets
from sklearn import svm
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
import warnings
warnings.filterwarnings("ignore")


# Função que computa a função logística (sigmóide)
def sigmoide(row, w):
    yPred = 1/(1+np.exp(-row @ w))
    return yPred

# Função responsável para treinar o modelo de Regressão Logística via Gradiente Descendente
def fitRL(x, y, n_epochs, alpha):
    print("[Regressão Logística] Treinando modelo...")
    erroQM = []
    wPrev = np.zeros(x.shape[1]+1)
    aux = np.ones((x.shape[0], 1))
    x = np.hstack((aux, x))
    
    for epochs in range (0, n_epochs):
        suma = 0
        sumErro = 0
        for i in range(0, x.shape[0]):
            sumErro = sumErro + (y[i]-sigmoide(x[i],wPrev))**2
            suma = suma +  (y[i]-sigmoide(x[i],wPrev))*np.transpose(x[i])
        w = np.transpose(wPrev) + alpha*(1/x.shape[0])*suma
        erroEp = ((1/(2*x.shape[0]))*sumErro)
        erroQM.append(erroEp)
        wPrev = w
    return wPrev, erroQM

# Função responsável para predizer os dados
def predictRL(w, x):
    print("[Regressão Logística] Testando modelo...")
    yPredito = []
    aux = np.ones((x.shape[0], 1))
    x = np.hstack((aux, x))
    for row in x:
        if(sigmoide(row, w)>=0.5):
            yPredito.append(1)
        else:
            yPredito.append(0)
    return yPredito

# Função responsável para "treinar" que gera os dados estatísticos necessários para o modelo de 
# Análise de Discriminante Gaussiano
def fitAGD(x, y):
    print("[Análise Discriminante Gaussiana] Treinando modelo...")
    classes, ocorrencs = np.unique(y, return_counts=True) # pegando as classes e ocorrencias
    numClasses = len(classes) # numero de classes
    n = len(y) # numero de linhas do dataset
    numFeatures = x.shape[1] # numero de colunas do dataset
    
    # Probabilidade das classes será proporcional a frequencia dessa classe no dataset
    probabilidadeClasses = dict(zip(classes, ocorrencs))
    for key in probabilidadeClasses:
        probabilidadeClasses[key] = probabilidadeClasses[key] / n
    
    media = np.zeros((numFeatures, numClasses)) # criando a lista da media das features por classe
    covar = np.zeros((numFeatures, numFeatures, numClasses)) # criando a lista de matrizes de correlação das features para cada classe

    for classe in classes:
        xk = x[y == classe] # pega as linhas em que classe é igual ao y -> que aí eu acesso essas linhas do x
        classe = int(classe)
        media[:, int(classe)] = np.mean(xk, axis=0)
        xi_mean = xk - media[:, int(classe)]
        covar[:, :, int(classe)] = (np.transpose(xi_mean) @ xi_mean)/len(xk)
        covar[:, :, int(classe)] += np.eye(numFeatures) * np.mean(np.diag(covar[:,:,classe]))  * 10 ** -6 # ver se assim ta certo, pq o do cesar ele botou uns numeros que eu nao entendi
    return {'media': media, 'covar': covar, 'classes': classes, 'numRows': n, 'numClasses': numClasses, 'numFeatures': numFeatures, 'probabilidadeClasses': probabilidadeClasses }

# Função responsável para predizer a classe de um único registro
def predict1AGD(model, row):
    probabilits = np.zeros(model['numClasses'])
    for classe in model['classes']:
        classe = int(classe)
        fator1 = 1/((sqrt(np.linalg.det(model['covar'][:, :, classe])) * ((2*pi)**(model['numFeatures']/2)))+10**-6) 
        
        inversa = np.linalg.inv(model['covar'][:, :, classe])
        difXMedia = row - model['media'][:, classe]
        z = (-0.5) * (np.transpose(difXMedia) @ inversa @ difXMedia) # valor que fica dentro do exp
        probabilits[classe] = fator1 * np.exp(z)
    return model['classes'][np.argmax(probabilits)]
    
# Função utilizada para predizer as classes de um conjunto de registros
def predictAGD(model, x_test):
    print("[Análise Discriminante Gaussiana] Testando modelo...")
    yPredito = np.array([predict1AGD(model, row) for row in x_test])
    return yPredito

# Funções que realizam os cálculos de distância entre dois registros
def distance_euclidian(x1, x2):
    return sqrt(np.sum([abs(i - j) for i, j in zip(x1,x2)]))

def distance_manhattan(x1, x2):
    return np.sum([abs(i-j) for i, j in zip(x1,x2)])

# Função responsável por predizer a classe de um único registro
def predict1KNN(x, y, x_teste, k, function):
    classes = np.unique(y)
    results = []
    for i in range(0, x.shape[0]):
        results.append([function(x[i], x_teste), y[i]])
    results = sorted(results)
    dictClasses = {}
    for i in classes:
        dictClasses[i] = 0
    for i in range(0, k):
        for row in dictClasses.keys():
            if results[i][1] == row:
                dictClasses[row] += 1
    
    # retornar a chave que tem maior contagem
    
    minimus = [results[i][1] for i in range (0,k)]
    
    contClasses = [(x, minimus.count(x)) for x in set(minimus)]

    maximo = np.argmax(contClasses, axis=0)

    return contClasses[maximo[1]][0]

# Função utilizada para predizer as classes de um conjunto de registros
def predictKNN(x, y, x_test, function):
    print("[KNN] Treinando modelo...")
    lista_k = [3,5,7,9,11]
    hiperparamKNN = {'n_neighbors': lista_k}
    
    model = GridSearchCV(KNeighborsClassifier(), hiperparamKNN)
    
    model.fit(x, y)
    
    params = model.best_params_
    print("Parâmetros escolhidos para KNN: ", model.best_params_)
    
    print("[KNN] Testando modelo...")
    yPredito = [predict1KNN(x, y, row, model.best_params_['n_neighbors'], function) for row in x_test]
    return yPredito

# Função responsável por treinar a Árvore de Decisão e escolher os melhores hiperparâmetros por meio de grid-search
def fitAD(x, y, criterion, max_depth):
    print("[Árvore de Decisão] Selecionando hiperparâmetros...")
    listMaxDepth = range(1, 50)
    configTree = {'criterion':['gini','entropy'],'max_depth':listMaxDepth}
    clf = GridSearchCV(DecisionTreeClassifier(), configTree)
#     clf = DecisionTreeClassifier(criterion = criterion, max_depth = max_depth)
    
    print("[Árvore de Decisão] Treinando modelos...")
    clf.fit(x, y)
    
    params = clf.best_params_
    print("Parâmetros escolhidos para Árvore de Decisão: ", clf.best_params_)
    #tree = DecisionTreeClassifier(criterion = params['criterion'], max_depth=params['max_depth'])
    #return tree
    return clf

# Função que prediz a classe de um conjunto ou um único registro
def predictAD(tree, x, y, x_test):
    #tree.fit(x, y)   
    print("[Árvore de Decisão] Testando modelos...")
    yPredito = tree.predict(x_test)
    return yPredito

# Função responsável por treinar o SVM e escolher os melhores hiperparâmetros por meio de grid-search
def fitSVM(x, y):
    print("[SVM] Selecionando hiperparâmetros...")
    #     model = SVC(gamma='auto')
    configSVM = [{'kernel': ['rbf'], 'C': 2 ** np.arange(-5.0, 16.0, 2), 'gamma': 2 ** np.arange(-15.0, 4.0, 2)},
                 {'kernel':['poly'], 'C': 2 ** np.arange(-5.0, 16.0, 2),'degree': np.arange(2, 6)},
                 {'kernel': ['linear'], 'C': 2 ** np.arange(-5.0, 16.0, 2)}]

    model = GridSearchCV(SVC(), configSVM)
 
    print("[SVM] Treinando Modelo...")
    model.fit(x, y)
    print("[SVM] Hiperparâmetros escolhidos para SVM: ", model.best_params_)
    return model
    

# Função que prediz a classe de um conjunto ou um único registro
def predictSVM(svm, x, y, x_test):
    #svm.fit(x, y)
    print("[SVM] Testando Modelo...")
    yPredito = svm.predict(x_test)
    return yPredito

# Função responsável por treinar o Random Forest e escolher os melhores hiperparâmetros por meio de grid-search
def fitRF(x, y):
    print("[RANDOM FOREST] Selecionando hiperparâmetros...")
    listEstimators = range(100, 150)
    listMaxDepth = range(1, 10)
   
    configRandom = {'criterion':['gini','entropy'],'n_estimators':listEstimators, 'max_depth':listMaxDepth}
#     clf = RandomForestClassifier(criterion = criterion, n_estimators = n_estimators, max_depth=max_depth)
    clf = GridSearchCV(RandomForestClassifier(), configRandom)
    print("[RANDOM FOREST] Treinando modelo...")
    clf.fit(x,y)
    
    #params = clf.best_params_
    print("[RANDOM FOREST] Hiperparâmetros escolhidos para Radom Forest: ", clf.best_params_)
    
    #randomForest = RandomForestClassifier(criterion = params['criterion'], max_depth=params['max_depth'], n_estimators=params['n_estimators'])
    #return randomForest
    return clf

# Função que prediz a classe de um conjunto ou um único registro
def predictRF(randomForest, x, y, x_test):
    #randomForest.fit(x, y)
    print("[RANDOM FOREST] Testando modelo...")
    yPredito = randomForest.predict(x_test)
    return yPredito

