from numpy import array,cos,sin,exp,pi,fft,fabs,zeros_like,zeros,sqrt,max
from scipy.integrate import cumtrapz

def FourierAmplitude(data,dt):
    n = 1
    while n < len(data): n *= 2
    T = len(data)*dt
    fftx = abs(fft.fft(data,n))
    fa = (fftx[0:int(n/2+1)])*dt
    delf = 1/(n*dt)
    f = array(range(1,int(n/2+2)))*delf
    a_rms = (cumtrapz(data ** 2, dx=dt) / T)[-1] ** 0.5
    pa = (fa ** 2) / (pi * T * (a_rms ** 2))

    return f,fa,pa

def _get_time_series(const, omega2,num_steps,num_per,acceleration,dt):
    x_d = zeros([num_steps - 1, num_per], dtype=float)
    x_v = zeros_like(x_d)
    x_a = zeros_like(x_d)

    for k in range(0, num_steps - 1):
        dug = acceleration[k + 1] - acceleration[k]
        z_1 = const['f2'] * dug
        z_2 = const['f2'] * acceleration[k]
        z_3 = const['f1'] * dug
        z_4 = z_1 / dt

        if k == 0:
            b_val = z_2 - z_3
            a_val = (const['f5'] * b_val) + (const['f4'] * z_4)
        else:
            b_val = x_d[k - 1, :] + z_2 - z_3
            a_val = (const['f4'] * x_v[k - 1, :]) + (const['f5'] * b_val) + (const['f4'] * z_4)

        x_d[k, :] = (a_val * const['g1']) + (b_val * const['g2']) + z_3 - z_2 - z_1
        x_v[k, :] = (a_val * const['h1']) - (b_val * const['h2']) - z_4
        x_a[k, :] = (-const['f6'] * x_v[k, :]) - (omega2 * x_d[k, :])

    return x_a, x_v, x_d


def ResponseSpectra(acceleration, dt, periods, damping=0.05):
    omega = (2. * pi) / periods
    omega2 = omega ** 2.
    omega3 = omega ** 3.
    omega_d = omega * sqrt(1.0 - (damping ** 2.))

    const = {'f1': (2.0 * damping) / (omega3 * dt),
            'f2': 1.0 / omega2,
            'f3': damping * omega,
            'f4': 1.0 / omega_d}

    const['f5'] = const['f3'] * const['f4']
    const['f6'] = 2.0 * const['f3']
    const['e'] = exp(-const['f3'] * dt)
    const['s'] = sin(omega_d * dt)
    const['c'] = cos(omega_d * dt)
    const['g1'] = const['e'] * const['s']
    const['g2'] = const['e'] * const['c']
    const['h1'] = (omega_d * const['g2']) - (const['f3'] * const['g1'])
    const['h2'] = (omega_d * const['g1']) + (const['f3'] * const['g2'])
    x_a, x_v, x_d = _get_time_series(const, omega2,len(acceleration),len(periods),acceleration,dt)

    response_spectrum = {
        'Acceleration': max(fabs(x_a), axis=0),
        'Velocity': max(fabs(x_v), axis=0) * 981,
        'Displacement': max(fabs(x_d), axis=0) * 981}

    response_spectrum['Pseudo-Velocity'] = omega * response_spectrum['Displacement']
    response_spectrum['Pseudo-Acceleration'] = (omega ** 2.) * response_spectrum['Displacement']/981

    return response_spectrum
