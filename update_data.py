"""A little helper scripts to generate the requirements.txt and models.json with
the latest supported model versions based on the compatibility.json."""
from spacy.about import __compatibility__ as COMPAT_URL
from spacy.util import get_lang_class, is_compatible_version
from pathlib import Path
import requests
import typer
import srsly


URL_TEMPLATE = "https://github.com/explosion/spacy-models/releases/download/{name}-{version}/{name}-{version}.tar.gz#egg={name}=={version}"


def main(
    # fmt: off
    spacy_version: str = typer.Argument(">=3.0.0a40,<3.1.0", help="The spaCy version range"),
    spacy_streamlit_version: str = typer.Argument(">=1.0.0a3,<1.1.0", help="The version range of spacy-streamlit"),
    req_path: Path = typer.Option(Path(__file__).parent / "requirements.txt", "--requirements-path", "-rp", help="Path to requirements.txt"),
    desc_path: Path = typer.Option(Path(__file__).parent / "models.json", "--models-json-path", "-mp", help="Path to models.json with model details for dropdown"),
    package: str = typer.Option("spacy-nightly", "--package", "-p", help="The parent package (spacy, spacy-nightly, etc.)"),
    exclude: str = typer.Option("en_vectors_web_lg", "--exclude", "-e", help="Comma-separated model names to exclude"),
    # fmt: on
):
    exclude = [name.strip() for name in exclude.split(",")]
    r = requests.get(COMPAT_URL)
    r.raise_for_status()
    compat = r.json()["spacy"]
    data = None
    for version_option in compat:
        if is_compatible_version(version_option, spacy_version):
            data = compat[version_option]
            break
    if data is None:
        raise ValueError(f"No compatible models found for {spacy_version}")
    reqs = [
        f"# Auto-generated by {Path(__file__).name}",
        f"{package}{spacy_version}",
        f"spacy-streamlit{spacy_streamlit_version}",
    ]
    models = {}
    for model_name, model_versions in data.items():
        if model_name not in exclude and model_versions:
            reqs.append(URL_TEMPLATE.format(name=model_name, version=model_versions[0]))
            lang = model_name.split("_", 1)[0]
            lang_name = get_lang_class(lang).__name__
            models[model_name] = f"{lang_name} ({model_name})"
    with Path(req_path).open("w", encoding="utf8") as f:
        f.write("\n".join(reqs))
    srsly.write_json(desc_path, models)
    print(f"Generated requirements.txt and models.json for {len(reqs) - 1} models")


if __name__ == "__main__":
    typer.run(main)
