import math
import os
import random
import sys
import time

class LIFNeuron:
    """Leaky Integrate-and-Fire (LIF) Spiking Neuron Model."""
    def __init__(self, name, tau_m=10.0, v_rest=-65.0, v_thresh=-50.0, v_reset=-70.0, r_m=10.0):
        self.name = name
        self.tau_m = tau_m        # Membrane time constant (ms)
        self.v_rest = v_rest      # Resting membrane potential (mV)
        self.v_thresh = v_thresh  # Firing threshold (mV)
        self.v_reset = v_reset    # Post-spike reset potential (mV)
        self.r_m = r_m            # Membrane resistance (MOhm)
        self.v = v_rest
        self.spike_count = 0
        self.history = []

    def step(self, i_syn, dt=1.0):
        # dV/dt = (-(V - V_rest) + R_m * I_syn) / tau_m
        dv = (-(self.v - self.v_rest) + self.r_m * i_syn) * (dt / self.tau_m)
        self.v += dv

        spiked = False
        if self.v >= self.v_thresh:
            spiked = True
            self.spike_count += 1
            self.v = self.v_reset

        self.history.append("|" if spiked else ".")
        if len(self.history) > 48:
            self.history.pop(0)
        return spiked

def run_snn_demo():
    os.system("")
    # 3 Sensory Input LIF Neurons -> 1 Output Integration LIF Neuron
    sensors = [
        LIFNeuron("SENS-0 (Alpha)", tau_m=8.0),
        LIFNeuron("SENS-1 (Beta) ", tau_m=11.0),
        LIFNeuron("SENS-2 (Gamma)", tau_m=14.0),
    ]
    output_neuron = LIFNeuron("OUT-0  (Integr)", tau_m=9.0, v_thresh=-52.0)
    synaptic_weights = [3.2, 2.8, 3.5]

    tick = 0
    sys.stdout.write("\x1b[2J\x1b[?25l")
    try:
        while True:
            # Oscillating external stimulus currents (nA)
            currents = [
                1.6 + 0.9 * math.sin(tick / 10.0) + random.uniform(0, 0.4),
                1.5 + 0.9 * math.cos(tick / 13.0) + random.uniform(0, 0.4),
                1.7 + 0.8 * math.sin(tick / 7.0) + random.uniform(0, 0.4),
            ]

            syn_current_to_out = 0.0
            for idx, neuron in enumerate(sensors):
                if neuron.step(currents[idx]):
                    syn_current_to_out += synaptic_weights[idx]

            output_neuron.step(syn_current_to_out)

            lines = [
                "\x1b[1;36m==========================================================================\x1b[0m",
                f"\x1b[1;37m  UNICORE SNN LAB // LEAKY INTEGRATE-AND-FIRE (LIF)  |  t = {tick} ms\x1b[0m",
                "\x1b[1;36m==========================================================================\x1b[0m",
                "  Neuron            V_mem (mV)   Spikes   Spike Raster (| = Spike, . = Sub)",
                "\x1b[1;36m--------------------------------------------------------------------------\x1b[0m",
            ]

            for n in sensors + [output_neuron]:
                raster = "".join(n.history).replace("|", "\x1b[1;32m|\x1b[0m")
                color = "\x1b[33m" if n != output_neuron else "\x1b[1;35m"
                lines.append(
                    f"  {color}{n.name}\x1b[0m   {n.v:>7.2f} mV   {n.spike_count:>6}   [{raster:<48}]"
                )

            lines.append("\x1b[1;36m==========================================================================\x1b[0m")
            lines.append("  Pure Python LIF temporal dynamics | Press Ctrl+C to exit")

            sys.stdout.write("\x1b[H" + "\n".join(lines) + "\n")
            sys.stdout.flush()
            tick += 1
            time.sleep(0.08)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h\x1b[0m\n")

if __name__ == "__main__":
    run_snn_demo()
