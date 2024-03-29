from abc import ABCMeta, abstractmethod
import sys

import numpy as np

from config.configuration import Configuration
from simulator.environment import Environment


class FitnessEvaluatorFactory:
    DEFAULT = "default"

    @staticmethod
    def make_fitness_evaluator(genome_length, evaluator=DEFAULT):
        '''
        Factory method create object by the supplied string argument, evaluator.
        Configurations are also retrieved and supplied as a kwarg argument for the object.
        '''
        selected = Configuration.get()["fitness"][evaluator]
        config = selected["parameters"]
        return getattr(sys.modules[__name__], selected["class_name"])(genome_length, **config)


class AbstractFitnessEvaluator(metaclass=ABCMeta):
    '''
    All fitness evaluators must inherit from AbstractFitnessEvaluator, implement abstract methods and
    be registered in config.json to be acceptable as a fitness evaluator
    '''

    def __init__(self, genome_length, **kwargs):
        pass

    @abstractmethod
    def evaluate(self, individual):
        '''
        Evaluate must set the fitness of the individual.
        '''
        pass

    def evaluate_all(self, population):
        '''
        Convenience method for evaluating all individuals in the population list.
        '''
        for individual in population:
            individual.fitness = self.evaluate(individual)


class DefaultFitnessEvaluator(AbstractFitnessEvaluator):
    '''
    One max fitness evaluator. Heuristic that measure how similar a bit vector is to
    a target vector. The target vector defaults to containing just 1's, and therefore called the
    One max problem.
    '''


    def __init__(self, genome_length, random_target=False):
        if random_target:
            self.target = np.random.randint(2, size=genome_length)
            print("RANDOM TARGET: ", self.target)
        else:
            self.target = np.ones(genome_length, dtype=np.int)

    def evaluate(self, individual):
        '''
        Return the fraction of where the phenotype correspond to the target vector.
        Use not xor --> ==
        '''
        p = individual.phenotype_container.phenotype
        #TODO: should individual have it's own ann or weights added to ann here?

        d = np.sum(np.logical_not(np.logical_xor(p, self.target), dtype=np.bool))
        return (d / p.size)


class FlatlandsAgentFitnessEvaluator(AbstractFitnessEvaluator):
    '''
    Flatlands agent evaluator. Heuristic that measure how well individuals
    configure a ann that maximize food eaten while minimizing the poison.
    '''

    def __init__(self, genome_length, dynamic=False, number_of_scenarios=5, grid_dimension=10):
        self.dynamic = dynamic
        self.nr_of_scenarios = number_of_scenarios
        self.dim = grid_dimension
        self.fd = 0.33333
        self.pd = 0.33333


        self.scenarios = [Environment(self.dim, f_prob=self.fd, p_prob=self.pd) for i in range(number_of_scenarios)]

    def evaluate_all(self, population):
        '''
        Overriden from super class. Environment has to be replaced if
        the dynamic option is chosen.
        '''
        if self.dynamic:
            #TODO: Maybe create method that replace board, avoid object initalizations
            self.scenarios = [Environment(self.dim,f_prob=self.fd, p_prob=self.pd) for i in range(self.nr_of_scenarios)]

        for individual in population:
            individual.fitness = self.evaluate(individual)

    def evaluate(self, individual):
        '''
        Returns a score that penalize poison and rewards food eating. Eating poison is bad but is weighted slightly less
        than eating food. The ANN is retrieved with the weights developed from the individuals genotype. The ANN is tested
        on n scenarios. If the system is configured to dynamic new scenarios are made for each iteration.
        '''
        p = individual.phenotype_container.get_ANN()
        scoring = [e.score_agent(p) for e in self.scenarios]
        score = sum(fs/(1+(ps*.8)) for fs, ps in scoring)/len(self.scenarios)
        return score