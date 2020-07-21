from numpy import eye, dot, sum, tile, linalg
from numpy.linalg import inv

class KalmanFilter():
    def __init__(self, X, P, A, Q, B, H, R):
        """
        X: The mean state estimate of the previous step (k-1).
        P: The state covariance of previous step (k-1).
        A: The transition nxn matrix.
        Q: The process noise covariance matrix.
        B: The input effect matrix.
        U: The control input
        """
        self.X = X
        self.P = P
        self.A = A
        self.Q = Q
        self.B = B
        self.H = H
        self.R = R
    
    def predict(self):
        # predicted state estimate
        self.X = self.A @ self.X# + self.B @ U
        # predicted covariance estimate
        self.P = self.A @ (self.P @ self.A.T) + self.Q
        return self.X
    
    def update(self, z):
        """
        K: the Kalman Gain matrix
        IM: the Mean of predictive distribution of Y
        IS: the Covariance or predictive mean of Y
        LH: the Predictive probability (likelihood) of measurement which is computed using the Python function gauss_pdf. 
        """
        # Innovation      
        y = z - self.H @ self.X
        # Innovation covariance
        IS = self.H @ self.P @ self.H.T + self.R
        # Kalman gain
        K = self.P @ (self.H.T @ inv(IS))
        # updated state
        self.X += K @ y
        # updated covariance
        self.P = (eye(self.X.shape[0]) - K @ self.H) @ self.P
        
        return self.X, self.P
    
    def gauss_pdf(self, X, M, S):
        if M.shape()[1] == 1:
            DX = X - tile(M, X.shape()[1])
            E = 0.5 * sum(DX * (dot(inv(S), DX)), axis=0)
            E = E + 0.5 * M.shape()[0] * log(2 * pi) + 0.5 * log(det(S))
            P = exp(-E)
        elif X.shape()[1] == 1:
            DX = tile(X, M.shape()[1])- M
            E = 0.5 * sum(DX * (dot(inv(S), DX)), axis=0)
            E = E + 0.5 * M.shape()[0] * log(2 * pi) + 0.5 * log(det(S))
            P = exp(-E)
        else:
            DX = X-M
            E = 0.5 * dot(DX.T, dot(inv(S), DX))
            E = E + 0.5 * M.shape()[0] * log(2 * pi) + 0.5 * log(det(S))
            P = exp(-E)
    