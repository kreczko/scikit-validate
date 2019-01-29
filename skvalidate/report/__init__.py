import os
from importlib import import_module

import json
import yaml
from jinja2 import Template
from jinja2.exceptions import TemplateSyntaxError, UndefinedError

from .. import __skvalidate_root__
from ..compare import compare_metrics


def make_report(config):
    pass


class Report(object):
    """Compiles a report in Markdown format."""

    def __init__(self, yaml_config):
        """Create a report from a yaml config.

        @param yamlConfig: yaml config dictionary
        """
        self.__general = Section(section_name='general', **yaml_config)

    @staticmethod
    def from_yaml(path):
        """Create Report from YAML config"""
        config = read_config(path)
        return Report(config)

    def write(self, output_file):
        """Write report to outputfile

        @param output_file: file to write Report to
        """
        content = self.__general.content
        with open(output_file, 'w') as f:
            f.write(content)

    def __repr__(self):
        """Return string representation of Report"""
        repr = 'Output file: {}\n'
        repr += 'Template: {}\n'
        repr += 'Properties: {}\n'
        repr += 'Sections:\n {}'

        return repr.format(
            self.__output_file,
            self.__template,
            str(self.__values),
            '\n'.join(__repr_section__(k, v) for k, v in self.__sections.items()))


class Section(object):
    """Class to encapsulate configuration for a section of a report"""

    def __init__(self, section_name, **kwargs):
        """Create Section instance from a name and a dictionary

        @param section_name: name of the section
        @param kwargs: dictionary of content of the section
        """
        sections = kwargs.pop('sections', {})
        self.__template = kwargs.pop('template')
        self.__name = section_name
        # TODO: not just general
        __check_template__(self.__template, 'general')
        # everything else is a property
        self.__properties = kwargs
        self.__values = {}
        self.__sections = {}
        self.__filled = False
        self.__content = ''

        for name, content in sections.items():
            self.__sections[name] = Section(section_name=name, **content)

    def __fill__(self):
        """Read template and fill with values"""
        with open(self.__template) as f:
            self.__content = Template(f.read())

        for name, content in self.__properties.items():
            value = __fill_property__(name, content)
            self.__values.update(value)

        for name, section in self.__sections.items():
            self.__values[name] = section.content
        self.__content = self.__content.render(
            **self.__values
        )
        self.__filled = True

    @property
    def content(self):
        """Return entire content of the section"""
        if not self.__filled:
            try:
                self.__fill__()
            except (UndefinedError, TemplateSyntaxError, TypeError) as e:
                print('Unable to render section "{}": {}'.format(self.__name, e))
                print('Section values:', self.__values)
        return self.__content


def read_config(path):
    with open(path) as f:
        config_tpl = Template(f.read())
    config = config_tpl.render(scikit_validate=__skvalidate_root__)
    config = yaml.load(config)
    return config


def __check_template__(path, section):
    if not os.path.exists(path):
        raise IOError('Could not find template "{}" for section {}'.format(path, section))


def __fill_property__(name, content):
    """Fill property with values from content.

    A property is a dictionary of the type
        {name: content}
    where the content can either be a value (e.g. string) or a function or
        {name: {function:<include for python function, param1:v1, param2:v2, ...}}

    @param name: name of the property
    @param: content: content of the property
    """
    if isinstance(content, dict):
        func_path = content.pop('function')
        tokens = func_path.split('.')
        func_module, func_name = '.'.join(tokens[:-1]), tokens[-1]
        params = content
        m = import_module(func_module)
        func = getattr(m, func_name)
        return {name: func(**params)}
    else:
        return {name: content}


def __repr_section__(name, section):
    repr = '  name: {}\n'
    repr += '  template: {}\n'
    repr += '  properties: {}\n'
    return repr.format(
        name,
        section.pop('template'),
        str(section),
    )

def get_metrics(metrics_json, metrics_ref_json, **kwargs):
    with open(metrics_json) as f:
        metrics = json.load(f)
    with open(metrics_ref_json) as f:
        metrics_ref = json.load(f)

    keys = kwargs.pop('keys', None)
    comparison = compare_metrics(metrics, metrics_ref, keys=keys)
    # format metrics
    symbol_up = kwargs.pop('symbol_up', '')
    symbol_down = kwargs.pop('symbol_down', '')
    symbol_same = kwargs.pop('symbol_same', '')

    for cmd, metrics in comparison.items():
        for name, metric in metrics.items():
            if isinstance(metric['diff'], str):
                metric['symbol'] = ''
                continue
            if metric['diff'] > 0:
                metric['symbol'] = symbol_up
            elif metric['diff'] < 0:
                metric['symbol'] = symbol_down
            else:
                metric['symbol'] = symbol_same

    return comparison