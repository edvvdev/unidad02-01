from inf8239_u02.modeling import build_models


def test_each_pipeline_predicts_one_label():
    texts = ["excelente servicio", "mala atención", "servicio rápido", "atención lenta"]
    labels = ["positive", "negative", "positive", "negative"]
    for model in build_models().values():
        model.fit(texts, labels)
        assert len(model.predict(["excelente atención"])) == 1
        assert "tfidf" in model.named_steps
        assert "model" in model.named_steps
