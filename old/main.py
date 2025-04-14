from simulation import Simulation

if __name__ == "__main__":
    s = Simulation()
    s.generate_galaxy(num_starting_civilizations=4)

    for _ in range(1000):
        s.process_tick()