import torch
import torch.nn as nn
import torchvision.datasets as dsets
import torchvision.transforms as transforms
from torch.autograd import Variable
import numpy
import time

train = [
    [5.0,3,0,1],
    [4,0,0,1],
    [1,1,0,5],
    [1,0,0,4],
    [0,1,5,4],
]

test = [
    [0,0,2,0],
    [0,2,2,0],
    [0,0,5,0],
    [0,1,5,0],
    [1,0,0,0],
]

N = len(train)
M = len(train[0])
K = 2

P = torch.tensor(numpy.random.rand(N,K))
Q = torch.tensor(numpy.random.rand(M,K))

# Hyper Parameters 
input_size = 2*K
hidden_size = 2*K
neumf_size = 3*K
output_size = 1
num_epochs = 5000
batch_size = 1
learning_rate = 0.001

# Dataset
train_dataset = torch.tensor(train)

# test_dataset = torch.tensor(test)


# Neural Network Model (1 hidden layer)
class Net(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(Net, self).__init__()
        self.layer1 = nn.Linear(input_size, hidden_size)
        self.layer2 = nn.Linear(hidden_size, hidden_size)
        self.layer3 = nn.Linear(hidden_size, hidden_size)
        self.layer4 = nn.Linear(hidden_size, hidden_size)
        self.layer5 = nn.Linear(hidden_size, hidden_size)
        self.layer6_mlp= nn.Linear(hidden_size, output_size)
        self.layer6_mf = nn.Linear(K, output_size)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        alpha = 0.7
        GMF = (x[0 : 2] * x[2 : 4]).float()
        MLP = x.view(x.numel()).float()
        out = self.layer1(MLP)
        out = self.relu(out)
        out = self.layer2(out)
        out = self.relu(out)
        out = self.layer3(out)
        out = self.relu(out)
        out = self.layer4(out)
        out = self.relu(out)
        out = self.layer5(out)
        out = self.relu(out)
        out = alpha * self.layer6_mf(GMF) + (1-alpha) * self.layer6_mlp(out)
        return out
    
# Loss and Optimizer
criterion = nn.L1Loss()  

def matrix_factorization(R, P, Q, K, steps=5000, alpha=0.0002, beta=0.02):
    for step in range(steps):
        for i in range(len(R)):
            for j in range(len(R[i])):
                if R[i][j] > 0:
                    eij = R[i][j] - (P[i]*Q[j]).sum()
                    P[i] = P[i] + alpha * (2 * eij * Q[j] - beta * P[i])
                    Q[j] = Q[j] + alpha * (2 * eij * P[i] - beta * Q[j])
    return P, Q

def matrix_completion(P, Q, net):
    R = []
    for i in range(len(P)):
        tmp = []
        for j in range(len(Q)):
            inputs = torch.cat((P[i],Q[j]), 0).cuda()
            outputs = net(inputs)
            tmp.append(outputs.item())
        R.append(tmp)
    return R

print(train_dataset)
start_time = time.time() 
nP, nQ = matrix_factorization(train_dataset, P, Q, K)
print("--- %s seconds ---" %(time.time() - start_time))
Y = nP.mm(nQ.t())
Y = Y.cuda()
print(Y)

net = Net(input_size, hidden_size, output_size)
net.cuda()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(net.parameters(), lr=learning_rate)

start_time = time.time() 
for i in range(len(Y)):
    for j in range(len(Y[0])):
        if Y[i][j] > 0:
            # Train the Model
            for epoch in range(num_epochs):
                # Forward + Backward + Optimize
                optimizer.zero_grad()  # zero the gradient buffer
                inputs = torch.cat((P[i],Q[j]), 0).cuda()
                outputs = net(inputs)
                loss = criterion(outputs, Y[i][j].float())
                loss.backward()
                optimizer.step()
print("--- %s seconds ---" %(time.time() - start_time))
print(matrix_completion(nP,nQ,net))
torch.save(net.state_dict(), 'model.pkl')
