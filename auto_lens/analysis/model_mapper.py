import math
from scipy.special import erfinv
import inspect
import configparser
import os
from auto_lens import exc

path = os.path.dirname(os.path.realpath(__file__))


class ModelMapper(object):
    """A collection of priors formed by passing in classes to be reconstructed
        @DynamicAttrs
    """

    def __init__(self, config=None, **classes):
        """
        Parameters
        ----------
        config: Config
            An object that wraps a configuration

        Examples
        --------
        # The ModelMapper converts a set of classes whose input attributes may be modeled using a non-linear search, to
        # parameters with priors attached.

        # A config is passed into the collection to provide default setup values for the priors:

        collection = ModelMapper(config)

        # All class instances that are to be generated by the collection are specified by passing their name and class:

        collection.add_class("sersic_1", light_profile.EllipticalSersicMass)
        collection.add_class("sersic_2", light_profile.EllipticalSersicMass)
        collection.add_class("other_instance", SomeClass)

        # A PriorModel instance is created each time we add a class to the collection. We can access those models using
        # their name:

        sersic_model_1 = collection.sersic_1

        # This allows us to replace the default priors:

        collection.sersic_1.intensity = GaussianPrior(2., 5.)

        # Or maybe we want to tie two priors together:

        collection.sersic_1.intensity = collection.sersic_2.intensity

        # This statement reduces the number of priors by one and means that the two sersic instances will always share
        # the same centre.

        # We can then create instances of every class for a unit hypercube vector with length equal to
        # len(collection.priors):

        model_instance = collection.model_instance_for_vector([.4, .2, .3, .1])

        # The attributes of the model_instance are named the same as those of the collection:

        sersic_1 = collection.sersic_1

        # But this attribute is an instance of the actual EllipticalSersicMass class

        # A ModelMapper can be concisely constructed using keyword arguments:

        collection = prior.ModelMapper(config, source_light_profile=light_profile.EllipticalSersicMass,
                                    lens_mass_profile=mass_profile.EllipticalCoredIsothermal,
                                    lens_light_profile=light_profile.EllipticalCoreSersic)
        """
        super(ModelMapper, self).__init__()

        self.config = (config if config is not None else Config("{}/../config".format(path)))

        for name, cls in classes.items():
            self.add_class(name, cls)

        self.total_parameters = len(self.priors_ordered_by_id)

    def add_classes(self, **kwargs):
        for key, value in kwargs.items():
            self.add_class(key, value)

        self.total_parameters = len(self.priors_ordered_by_id)

    def add_class(self, name, cls):
        """
        Add a class to this collection. Priors are automatically generated for __init__ arguments. Prior type and
        configuration is taken from matching module.class.attribute entries in the config.

        Parameters
        ----------
        name: String
            The name of this class. This is also the attribute name for the class in the collection and model_instance.
        cls: class
            The class for which priors are to be generated.

        Returns
        -------
        prior_model: PriorModel
            A prior_model instance for this class
        """
        if hasattr(self, name):
            raise exc.PriorException("Model mapper already has a prior model called {}".format(name))

        prior_model = PriorModel(cls, self.config)

        setattr(self, name, prior_model)
        return prior_model

    @property
    def prior_models(self):
        """
        Returns
        -------
        prior_model_tuples: [(String, PriorModel)]
        """
        return list(filter(lambda t: isinstance(t[1], AbstractPriorModel), self.__dict__.items()))

    @property
    def prior_set(self):
        """
        Returns
        -------
        prior_set: set()
            The set of all priors associated with this collection
        """
        # return {"{}_{}".format(name, prior[1]): prior for name, prior_model in self.prior_models for prior in
        #         prior_model.priors}.values()
        return {prior[1]: prior for name, prior_model in self.prior_models for prior in
                prior_model.priors}.values()

    @property
    def priors_ordered_by_id(self):
        """
        Returns
        -------
        priors: [Prior]
            An ordered list of unique priors associated with this collection
        """
        return sorted(list(self.prior_set), key=lambda prior: prior[1].id)

    @property
    def class_priors_dict(self):
        """
        Returns
        -------
        class_priors_dict: {String: [Prior]}
            A dictionary mapping the names of reconstructable class instances to lists of associated priors
        """
        return {name: prior_model.priors for name, prior_model in self.prior_models}

    def physical_vector_from_hypercube_vector(self, hypercube_vector):
        """
        Parameters
        ----------
        hypercube_vector: [float]
            A unit hypercube vector

        Returns
        -------
        values: [float]
            A vector with values output by priors
        """
        return list(map(lambda prior, unit: prior[1].value_for(unit), self.priors_ordered_by_id, hypercube_vector))

    def physical_values_ordered_by_class(self, hypercube_vector):
        model_instance = self.instance_from_unit_vector(hypercube_vector)
        result = []
        for instance_key in sorted(model_instance.__dict__.keys()):
            instance = model_instance.__dict__[instance_key]
            for attribute_key in sorted(instance.__dict__.keys()):

                value = instance.__dict__[attribute_key]
                if isinstance(value, tuple):
                    result.extend(list(value))
                else:
                    result.append(value)
        return result

    def physical_values_from_prior_medians(self):
        """
        Creates a ModelInstance, which has an attribute and class instance corresponding to every PriorModel attributed
        to this instance.

        This method uses the prior median values to setup the model_mapper instance.

        Returns
        -------
        model_instance : ModelInstance
            An object containing reconstructed model_mapper instances

        """
        return self.instance_from_unit_vector(unit_vector=[0.5] * len(self.prior_set))

    def instance_from_unit_vector(self, unit_vector):
        """
        Creates a ModelInstance, which has an attribute and class instance corresponding to every PriorModel attributed
        to this instance.

        This method takes as input a unit vector of parameter values, converting each to physical values via their \
        priors.

        Parameters
        ----------
        unit_vector: [float]
            A vector of physical parameter values.

        Returns
        -------
        model_instance : ModelInstance
            An object containing reconstructed model_mapper instances

        """
        arguments = dict(
            map(lambda prior, unit: (prior[1], prior[1].value_for(unit)), self.priors_ordered_by_id, unit_vector))

        return self.instance_from_arguments(arguments)

    def instance_from_physical_vector(self, physical_vector):
        """
        Creates a ModelInstance, which has an attribute and class instance corresponding to every PriorModel attributed
        to this instance.

        This method takes as input a physical vector of parameter values, thus omitting the use of priors.

        Parameters
        ----------
        physical_vector: [float]
            A unit hypercube vector

        Returns
        -------
        model_instance : ModelInstance
            An object containing reconstructed model_mapper instances

        """
        arguments = dict(
            map(lambda prior, physical_unit: (prior[1], physical_unit), self.priors_ordered_by_id, physical_vector))

        return self.instance_from_arguments(arguments)

    def mapper_from_gaussian_tuples(self, tuples):
        model_instance = ModelInstance()

        new_priors = map(lambda t: GaussianPrior(t[0], t[1]), tuples)
        arguments = dict(map(lambda prior, new_prior: (prior[1], new_prior), self.priors_ordered_by_id, new_priors))

        for prior_model in self.prior_models:
            setattr(model_instance, prior_model[0], prior_model[1].gaussian_prior_model_for_arguments(arguments))

        return model_instance

    def instance_from_arguments(self, arguments):
        """
        Creates a ModelInstance, which has an attribute and class instance corresponding to every PriorModel attributed
        to this instance.

        Parameters
        ----------
        arguments : dict
            The dictionary representation of prior and parameter values. This is created in the model_instance_from_* \
            routines.

        Returns
        -------
        model_instance : ModelInstance
            An object containing reconstructed model_mapper instances

        """

        model_instance = ModelInstance()

        for prior_model in self.prior_models:
            setattr(model_instance, prior_model[0], prior_model[1].instance_for_arguments(arguments))

        return model_instance

    def generate_model_info(self):
        """
        Use the priors that make up the model_mapper to information on each parameter of the overall model.

        This information is extracted from each priors *model_info* property.
        """

        model_info = ''

        for prior_name, prior_model in self.prior_models:

            model_info += prior_model.cls.__name__ + '\n' + '\n'

            for i, prior in enumerate(prior_model.priors):
                param_name = str(self.class_priors_dict[prior_name][i][0])
                model_info += param_name + ': ' + (prior[1].model_info + '\n')

            model_info += '\n'

        return model_info

    def output_model_info(self, filename):
        """Output a model information file, which lists the information of the model mapper (e.g. parameters, priors,
         etc.) """
        model_info = self.generate_model_info()
        with open(filename, 'w') as file:
            file.write(model_info)
        file.close()

    def check_model_info(self, filename):
        """Check whether the priors in this instance of the model_mapper are identical to those output into a model \
        info file on the hard-disk (e.g. from a previous non-linear search)."""

        model_info = self.generate_model_info()

        model_info_check = open(filename, 'r')

        if str(model_info_check.read()) != model_info:
            raise exc.PriorException(
                'The model_mapper input to MultiNest has a different prior for a parameter than the model_mapper '
                'existing in the files. Parameter = ')

        model_info_check.close()


prior_number = 0


class Prior(object):
    """An object used to map a unit value to an attribute value for a specific class attribute"""

    def __init__(self):
        global prior_number
        self.id = prior_number
        prior_number += 1

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return "<Prior id={}>".format(self.id)


class UniformPrior(Prior):
    """A prior with a uniform distribution between a lower and upper limit"""

    def __init__(self, lower_limit=0., upper_limit=1.):
        """

        Parameters
        ----------
        lower_limit: Float
            The lowest value this prior can return
        upper_limit: Float
            The highest value this prior can return
        """
        super(UniformPrior, self).__init__()
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

    def value_for(self, unit):
        """

        Parameters
        ----------
        unit: Float
            A unit hypercube value between 0 and 1
        Returns
        -------
        value: Float
            A value for the attribute between the upper and lower limits
        """
        return self.lower_limit + unit * (self.upper_limit - self.lower_limit)

    @property
    def model_info(self):
        """The line of text describing this prior for the model_mapper.info file"""
        return 'UniformPrior, lower_limit = ' + str(self.lower_limit) + ', upper_limit = ' + str(self.upper_limit)


class GaussianPrior(Prior):
    """A prior with a gaussian distribution"""

    def __init__(self, mean, sigma):
        super(GaussianPrior, self).__init__()
        self.mean = mean
        self.sigma = sigma

    def value_for(self, unit):
        """

        Parameters
        ----------
        unit: Float
            A unit hypercube value between 0 and 1
        Returns
        -------
        value: Float
            A value for the attribute biased to the gaussian distribution
        """
        return self.mean + (self.sigma * math.sqrt(2) * erfinv((unit * 2.0) - 1.0))

    @property
    def model_info(self):
        """The line of text describing this prior for the model_mapper.info file"""
        return 'GaussianPrior, mean = ' + str(self.mean) + ', sigma = ' + str(self.sigma)


class AbstractPriorModel:
    pass


class PriorModel(AbstractPriorModel):
    """Object comprising class and associated priors
        @DynamicAttrs
    """

    def __init__(self, cls, config=None):
        """
        Parameters
        ----------
        cls: class
            The class associated with this instance
        """

        self.cls = cls
        self.config = (config if config is not None else Config("{}/../config".format(path)))

        # TODO: Fix this
        arg_spec = inspect.getargspec(cls.__init__)

        try:
            defaults = dict(zip(arg_spec.args[-len(arg_spec.defaults):], arg_spec.defaults))
        except TypeError:
            defaults = {}

        args = arg_spec.args[1:]

        if 'settings' in defaults:
            del defaults['settings']
        if 'settings' in args:
            args.remove('settings')

        for arg in args:
            if arg in defaults and isinstance(defaults[arg], tuple):
                tuple_prior = TuplePrior()
                for i in range(len(defaults[arg])):
                    attribute_name = "{}_{}".format(arg, i)
                    setattr(tuple_prior, attribute_name, self.make_prior(attribute_name, cls))
                setattr(self, arg, tuple_prior)
            else:
                setattr(self, arg, self.make_prior(arg, cls))

    def make_prior(self, attribute_name, cls):
        config_arr = self.config.get_for_nearest_ancestor(cls, attribute_name)
        if config_arr[0] == "u":
            return UniformPrior(config_arr[1], config_arr[2])
        elif config_arr[0] == "g":
            return GaussianPrior(config_arr[1], config_arr[2])

    @property
    def tuple_priors(self):
        """
        Returns
        -------
        tuple_prior_tuples: [(String, TuplePrior)]
        """
        return list(filter(lambda t: isinstance(t[1], TuplePrior), self.__dict__.items()))

    @property
    def direct_priors(self):
        return list(filter(lambda t: isinstance(t[1], Prior), self.__dict__.items()))

    @property
    def priors(self):
        return [prior for tuple_prior in self.tuple_priors for prior in
                tuple_prior[1].priors] + self.direct_priors

    def instance_for_arguments(self, arguments):
        """
        Create an instance of the associated class for a set of arguments

        Parameters
        ----------
        arguments: {Prior: value}
            Dictionary mapping priors to attribute name and value pairs

        Returns
        -------
            An instance of the class
        """
        model_arguments = {t[0]: arguments[t[1]] for t in self.direct_priors}
        for tuple_prior in self.tuple_priors:
            model_arguments[tuple_prior[0]] = tuple_prior[1].value_for_arguments(arguments)
        return self.cls(**model_arguments)

    def gaussian_prior_model_for_arguments(self, arguments):
        new_model = PriorModel(self.cls, self.config)

        model_arguments = {t[0]: arguments[t[1]] for t in self.direct_priors}

        for tuple_prior in self.tuple_priors:
            setattr(new_model, tuple_prior[0], tuple_prior[1].gaussian_tuple_prior_for_arguments(arguments))
        for prior in self.direct_priors:
            setattr(new_model, prior[0], model_arguments[prior[0]])

        return new_model


class ListPriorModel(AbstractPriorModel):
    def __init__(self, prior_models, config=None):
        self.config = config
        self.prior_models = prior_models

    def instance_for_arguments(self, arguments):
        return [prior_model.instance_for_arguments(arguments) for prior_model in self.prior_models]

    @property
    def priors(self):
        return set([prior for prior_model in self.prior_models for prior in prior_model.priors])


class TuplePrior(object):
    @property
    def priors(self):
        return list(filter(lambda t: isinstance(t[1], Prior), self.__dict__.items()))

    def value_for_arguments(self, arguments):
        return tuple([arguments[prior[1]] for prior in self.priors])

    def gaussian_tuple_prior_for_arguments(self, arguments):
        tuple_prior = TuplePrior()
        for prior in self.priors:
            setattr(tuple_prior, prior[0], arguments[prior[1]])
        return tuple_prior


class ModelInstance(object):
    """
    @DynamicAttrs
    """
    pass


class Config(object):
    """Parses prior config"""

    def __init__(self, config_folder_path):
        """
        Parameters
        ----------
        config_folder_path: String
            The path to the prior config folder
        """
        self.path = config_folder_path
        self.parser = configparser.ConfigParser()

    def read(self, module_name):
        """
        Read a particular config file

        Parameters
        ----------
        module_name: String
            The name of the module for which a config is to be read (priors relate one to one with configs).
        """
        self.parser.read("{}/{}.ini".format(self.path, module_name.split(".")[-1]))

    def get_for_nearest_ancestor(self, cls, attribute_name):
        """
        Find a prior with the attribute name from the config for this class or one of its ancestors

        Parameters
        ----------
        cls: class
            The class of interest
        attribute_name: String
            The name of the attribute
        Returns
        -------
        prior_array: []
            An array describing this prior
        """

        def family(current_class):
            yield current_class
            for next_class in current_class.__bases__:
                for val in family(next_class):
                    yield val

        for family_cls in family(cls):
            if self.has(family_cls.__module__, family_cls.__name__, attribute_name):
                return self.get(family_cls.__module__, family_cls.__name__, attribute_name)

        ini_filename = cls.__module__.split(".")[-1]
        raise exc.PriorException(
            "The prior config at {}/{} does not contain {} in {} or any of its parents".format(self.path,
                                                                                               ini_filename,
                                                                                               attribute_name,
                                                                                               cls.__name__
                                                                                               ))

    def get(self, module_name, class_name, attribute_name):
        """

        Parameters
        ----------
        module_name: String
            The name of the module
        class_name: String
            The name of the class
        attribute_name: String
            The name of the attribute

        Returns
        -------
        prior_array: []
            An array describing a prior
        """
        self.read(module_name)
        arr = self.parser.get(class_name, attribute_name).replace(" ", "").split(",")
        return [arr[0]] + list(map(float, arr[1:]))

    def has(self, module_name, class_name, attribute_name):
        """
        Parameters
        ----------
        module_name: String
            The name of the module
        class_name: String
            The name of the class
        attribute_name: String
            The name of the attribute

        Returns
        -------
        has_prior: bool
            True iff a prior exists for the module, class and attribute
        """
        self.read(module_name)
        return self.parser.has_option(class_name, attribute_name)
