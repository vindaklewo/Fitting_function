import numpy as np

'''
以Python语言实现了一个mini-batch随机梯度下降反向传播神经网络，带冲量和学习率衰减功能。
'''

class DNN:
    def __init__(self, input_shape, shape, activations, eta=0.1, threshold=1e-5, softmax=False, max_epochs=1000,
                 regularization=0.001, minibatch_size=5, momentum=0.9, decay_power=0.5, verbose=False):

        if not len(shape) == len(activations):
            raise Exception("activations must equal to number od layers.")

        self.depth = len(shape)
        self.activity_levels = [np.mat([0])] * self.depth
        self.outputs = [np.mat(np.mat([0]))] * (self.depth + 1)
        self.deltas = [np.mat(np.mat([0]))] * self.depth
        self.eta = float(eta)
        self.effective_eta = self.eta
        self.threshold = float(threshold)
        self.max_epochs = int(max_epochs)
        self.regularization = float(regularization)
        self.is_softmax = bool(softmax)
        self.verbose = bool(verbose)
        self.minibatch_size = int(minibatch_size)
        self.momentum = float(momentum)
        self.decay_power = float(decay_power)
        self.iterations = 0
        self.epochs = 0

        self.activations = activations
        self.activation_func = []
        self.activation_func_diff = []
        for f in activations:

            if f == "sigmoid":
                self.activation_func.append(np.vectorize(self.sigmoid))
                self.activation_func_diff.append(np.vectorize(self.sigmoid_diff))
            elif f == "identity":
                self.activation_func.append(np.vectorize(self.identity))
                self.activation_func_diff.append(np.vectorize(self.identity_diff))
            elif f == "relu":
                self.activation_func.append(np.vectorize(self.relu))
                self.activation_func_diff.append(np.vectorize(self.relu_diff))
            else:
                raise Exception("activation function {:s}".format(f))

        self.weights = [np.mat(np.mat([0]))] * self.depth
        self.biases = [np.mat(np.mat([0]))] * self.depth
        self.acc_weights_delta = [np.mat(np.mat([0]))] * self.depth
        self.acc_biases_delta = [np.mat(np.mat([0]))] * self.depth

        self.weights[0] = np.mat(np.random.random((shape[0], input_shape)) / 100)
        self.biases[0] = np.mat(np.random.random((shape[0], 1)) / 100)
        for idx in np.arange(1, len(shape)):
            self.weights[idx] = np.mat(np.random.random((shape[idx], shape[idx - 1])) / 100)
            self.biases[idx] = np.mat(np.random.random((shape[idx], 1)) / 100)

    def compute(self, x):
        result = x
        for idx in np.arange(0, self.depth):
            self.outputs[idx] = result
            al = self.weights[idx] * result + self.biases[idx]
            self.activity_levels[idx] = al
            result = self.activation_func[idx](al)

        self.outputs[self.depth] = result
        return self.softmax(result) if self.is_softmax else result

    def predict(self, x):
        return self.compute(np.mat(x).T).T.A

    def bp(self, d):
        tmp = d.T

        for idx in np.arange(0, self.depth)[::-1]:
            delta = np.multiply(tmp, self.activation_func_diff[idx](self.activity_levels[idx]).T)
            self.deltas[idx] = delta
            tmp = delta * self.weights[idx]

    def update(self):

        self.effective_eta = self.eta / np.power(self.iterations, self.decay_power)

        for idx in np.arange(0, self.depth):
            # current gradient
            weights_grad = -self.deltas[idx].T * self.outputs[idx].T / self.deltas[idx].shape[0] + \
                           self.regularization * self.weights[idx]
            biases_grad = -np.mean(self.deltas[idx].T, axis=1) + self.regularization * self.biases[idx]

            # accumulated delta
            self.acc_weights_delta[idx] = self.acc_weights_delta[
                                              idx] * self.momentum - self.effective_eta * weights_grad
            self.acc_biases_delta[idx] = self.acc_biases_delta[idx] * self.momentum - self.effective_eta * biases_grad

            self.weights[idx] = self.weights[idx] + self.acc_weights_delta[idx]
            self.biases[idx] = self.biases[idx] + self.acc_biases_delta[idx]

    def fit(self, x, y):
        x = np.mat(x)
        y = np.mat(y)
        loss = []
        self.iterations = 0
        self.epochs = 0
        start = 0
        train_set_size = x.shape[0]

        while True:

            end = start + self.minibatch_size
            minibatch_x = x[start:end].T
            minibatch_y = y[start:end].T

            yp = self.compute(minibatch_x)
            d = minibatch_y - yp

            if self.is_softmax:
                loss.append(np.mean(-np.sum(np.multiply(minibatch_y, np.log(yp + 1e-1000)), axis=0)))
            else:
                loss.append(np.mean(np.sqrt(np.sum(np.power(d, 2), axis=0))))

            self.iterations += 1
            start = (start + self.minibatch_size) % train_set_size

            if self.iterations % train_set_size == 0:
                self.epochs += 1
                mean_e = np.mean(loss)
                loss = []

                if self.verbose:
                    print("epoch: {:d}. mean loss: {:.6f}. learning rate: {:.8f}".format(self.epochs, mean_e,
                                                                                         self.effective_eta))

                if self.epochs >= self.max_epochs or mean_e < self.threshold:
                    break

            self.bp(d)
            self.update()

    @staticmethod
    def sigmoid(x):
        return 1.0 / (1.0 + np.power(np.e, min(-x, 1e2)))

    @staticmethod
    def sigmoid_diff(x):
        return np.power(np.e, min(-x, 1e2)) / (1.0 + np.power(np.e, min(-x, 1e2))) ** 2

    @staticmethod
    def relu(x):
        return x if x > 0 else 0.0

    @staticmethod
    def relu_diff(x):
        return 1.0 if x > 0 else 0.0

    @staticmethod
    def identity(x):
        return x

    @staticmethod
    def identity_diff(x):
        return 1.0

    @staticmethod
    def softmax(x):
        x[x > 1e2] = 1e2
        ep = np.power(np.e, x)
        return ep / np.sum(ep, axis=0)


