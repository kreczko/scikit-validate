import os

from jinja2 import Template
from jinja2.exceptions import TemplateSyntaxError, UndefinedError

from .. import __skvalidate_root__
from .. import logger
from ..git import get_current_branch

TEMPLATE = os.path.join(__skvalidate_root__, 'data/templates/report/default/cpp_check_format.md')


def create_report(repository, changed_files, output_file, report_file):
    is_ci = os.environ.get('GITLAB_CI', None)
    path_and_cmd = 'cat ' + os.path.abspath(output_file)
    target_branch = 'master'
    source_branch = get_current_branch(repository)
    if is_ci:
        CI_PROJECT_URL = os.environ.get('CI_PROJECT_URL')
        CI_JOB_ID = os.environ.get('CI_JOB_ID')
        path_and_cmd = 'curl ${CI_PROJECT_URL}/-/jobs/${CI_JOB_ID}/artifacts/raw/{output_file}'
        path_and_cmd.format(CI_PROJECT_URL=CI_PROJECT_URL, CI_JOB_ID=CI_JOB_ID, output_file=output_file)
        target_branch = os.environ.get('CI_MERGE_REQUEST_TARGET_BRANCH_NAME')
        source_branch = os.environ.get('CI_COMMIT_REF_NAME')
    path_and_cmd = '{0} | git am'.format(path_and_cmd)

    with open(TEMPLATE) as f:
        template = Template(f.read())

    values = dict(
        changed_files=changed_files,
        path_and_cmd=path_and_cmd,
        source_branch=source_branch,
        target_branch=target_branch,
    )
    try:
        content = template.render(**values)
        with open(report_file, 'w') as f:
            f.write(content)

    except (UndefinedError, TemplateSyntaxError, TypeError) as e:
        logger.error('Unable to render cpp_check_format report: {}'.format(e))
        logger.error('Values: {0}'.format(values))
        raise e
