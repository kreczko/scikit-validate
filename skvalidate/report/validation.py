import os

from jinja2 import Template
import markdown2

from .. import __skvalidate_root__

from .. import compare
from .. import gitlab


def produce_validation_report(stages, jobs, validation_json, **kwargs):
    download_json = dict(validation_json=validation_json)
    jobs = gitlab.get_jobs_for_stages(stages, download_json=download_json, job_filter=jobs)
    data = {}
    for name, job in jobs.items():
        outputs = download_validation_outputs(job)
        data[name] = job['validation_json'][name]
        data[name]['distributions'].update(outputs)
        validation_output_file = 'validation_report_{0}.html'.format(name)
        details = create_detailed_report(data[name], output_dir='.', output_file=validation_output_file)
        data[name]['web_url_to_details'] = details
    summary = create_summary(data)
    return summary


def download_validation_outputs(job):
    name = job['name']
    data = job['validation_json'][name]
    base_output_dir = os.path.join(data['output_path'], name)
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)

    distributions = data[name]['distributions']
    results = {}
    for d_name, info in distributions.items():
        if 'image' not in info:
            continue
        image = info['image']
        output_file = image.replace(data['output_path'], base_output_dir)
        gitlab.download_artifact(job['id'], image, output_file=output_file)
        results[d_name] = {'image': output_file}
    return results


def create_detailed_report(data, output_dir='.', output_file='validation_report_detail.html'):
    """Create detailed report (with plots)"""
    template = os.path.join(__skvalidate_root__, 'data', 'templates', 'report', 'default', 'validation_detail.md')
    with open(template) as f:
        content = f.read()
    content = _add_table_of_contents(content, data)

    full_path = os.path.join(os.path.abspath(output_dir), output_file)
    with open(full_path, 'w') as f:
        f.write(content)
    local = 'CI' not in os.environ
    if local:
        protocol = 'file://'
        link = protocol + os.path.join(os.path.abspath(output_dir), output_file)
    else:
        link = gitlab.get_artifact_url(os.path.join(output_dir, output_file))
    return link


def create_summary(data):
    """Create validation summary."""
    summary = {}
    for name, info in data.items():
        distributions = info['distributions']
        status = compare.SUCCESS

        failed = info[compare.FAILED]
        error = info[compare.ERROR]
        unknown = info[compare.UNKNOWN]
        n_bad = len(failed) + len(error)

        if n_bad > 0:
            status = compare.FAILED
        summary[name] = dict(
            status=status,
            differ=failed,
            unknown=unknown,
            error=error,
            distributions=distributions.keys(),
            web_url_to_details=info['web_url_to_details'],
        )
    return summary


def _add_table_of_contents(content, data):
    template = Template(content)
    data['table_of_contents'] = ''
    tmp = template.render(**data)
    tmp = markdown2.markdown(tmp, extras=["toc"])
    table_of_contents = tmp.toc_html

    template = Template(content)
    data['table_of_contents'] = table_of_contents
    tmp = template.render(**data)
    return markdown2.markdown(tmp)
