import argparse
import dworp
import logging
import numpy as np


class Household(dworp.Agent):
    """Household agent for Schelling Segregation model"""
    def __init__(self, agent_id, color, x, y, similarity):
        super().__init__(agent_id, 0)
        self.color = color
        self.x = x
        self.y = y
        self.happy = None
        self.similarity = similarity

    def __repr__(self):
        return "Household({}, {}, ({},{}), happy={})".format(
            self.agent_id, self.color, self.x, self.y, self.happy)

    def init(self, start_time, env):
        self.happy = self.check_happiness(env)

    def step(self, new_time, env):
        if not self.check_happiness(env):
            env.move(self)

    def complete(self, current_time, env):
        self.happy = self.check_happiness(env)

    def check_happiness(self, env):
        """Check neighbors' color"""
        neighbors = env.grid.neighbors(self.x, self.y)
        similar = sum([neighbor.color == self.color for neighbor in neighbors])
        total = len(neighbors)
        return similar >= self.similarity * total


class ColorAssigner:
    """Assigns a color to a household probabilistically"""
    def __init__(self, rng, color1, color2):
        self.rng = rng
        self.color1 = color1
        self.color2 = color2

    def assign(self):
        if self.rng.uniform() < 0.5:
            return self.color1
        else:
            return self.color2


class HouseholdFactory:
    """Creates households as needed"""
    def __init__(self, rng, similarity, color1="blue", color2="orange"):
        self.namer = dworp.IdentifierHelper.get()
        self.similarity = similarity
        self.colorer = ColorAssigner(rng, color1, color2)

    def create(self, x, y):
        return Household(next(self.namer), self.colorer.assign(), x, y, self.similarity)


class SegregationEnvironment(dworp.Environment):
    """Segregation environment that holds the grid"""
    def __init__(self, grid, rng):
        super().__init__(0)
        self.grid = grid
        self.rng = rng

    def move(self, agent):
        x1 = x2 = agent.x
        y1 = y2 = agent.y
        while self.grid.occupied(x2, y2):
            x2 = self.rng.randint(0, self.grid.width)
            y2 = self.rng.randint(0, self.grid.height)
        self.grid.move(agent, x1, y1, x2, y2)
        agent.x = x2
        agent.y = y2

    def init(self, start_time):
        pass

    def step(self, new_time, agents):
        pass


class StdoutObserver(dworp.Observer):
    """Writes simulation state to stdout"""
    def start(self, time, agents, env):
        print("Starting: {}% agents happy".format(self.get_happiness(agents)))

    def step(self, time, agents, env):
        print("Step {}: {}% agents happy".format(time, self.get_happiness(agents)))

    def done(self, agents, env):
        print("Ending: {}% agents happy".format(self.get_happiness(agents)))

    @staticmethod
    def get_happiness(agents):
        num_happy = sum(agent.happy for agent in agents)
        return 100 * num_happy / float(len(agents))


class SegregationParams:
    """Container for simulation parameters"""
    def __init__(self, density, similarity, grid_size, seed, steps):
        self.density = density
        self.similarity = similarity
        self.grid_width = grid_size[0]
        self.grid_height = grid_size[1]
        self.seed = seed
        self.steps = steps


class SegregationSimulation(dworp.DoubleStageSimulation):
    """Simulation with two stages (moving and then happiness test)"""
    def __init__(self, params, observer):
        self.params = params
        self.rng = np.random.RandomState(seed)
        factory = HouseholdFactory(self.rng, params.similarity)
        time = dworp.BasicTime(params.steps)
        scheduler = dworp.RandomOrderScheduler()

        agents = []
        grid = dworp.Grid(params.grid_width, params.grid_height)
        env = SegregationEnvironment(grid, self.rng)
        for x in range(params.grid_width):
            for y in range(params.grid_height):
                if self.rng.uniform() < params.density:
                    agent = factory.create(x, y)
                    grid.set(agent, x, y)
                    agents.append(agent)

        super().__init__(agents, env, time, scheduler, observer)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)

    # parse command line parameters
    parser = argparse.ArgumentParser()
    parser.add_argument("--density", help="density of agents (1-99)", default=95, type=int)
    parser.add_argument("--similar", help="desired similarity (0-100)", default=30, type=int)
    parser.add_argument("--size", help="grid size formatted as XXXxYYY", default="50x50")
    parser.add_argument("--seed", help="seed of RNG", default=42, type=int)
    parser.add_argument("--steps", help="Number of time steps", default=10, type=int)
    args = parser.parse_args()

    # prepare parameters of simulation
    assert(1 <= args.density <= 99)
    assert(0 <= args.similar <= 100)
    density = args.density / float(100)
    similarity = args.similar / float(100)
    grid_size = [int(dim) for dim in args.size.split("x")]
    seed = args.seed
    steps = args.steps
    params = SegregationParams(density, similarity, grid_size, seed, steps)

    # create and run one realization of the simulation
    sim = SegregationSimulation(params, StdoutObserver())
    sim.run()