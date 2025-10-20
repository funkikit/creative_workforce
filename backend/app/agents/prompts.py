from __future__ import annotations

from textwrap import dedent


TEXT_PROMPTS: dict[str, str] = {
    "overall_spec": dedent(
        """
        あなたはプロジェクト「{project_name}」の全体企画書を作成します。
        世界観、主要キャラクター、長期的な物語構成を Markdown 形式で整理してください。
        セクション構成は「舞台設定」「キャラクター」「ストーリー展開」とし、追加指示があれば反映してください: {instructions}
        """
    ).strip(),
    "character_design": dedent(
        """
        プロジェクト「{project_name}」の主要キャラクター設定資料を作成してください。
        外見・性格・衣装・特徴的なポーズを Markdown の箇条書きでまとめてください。
        既存設定: {existing_summary}。追加指示: {instructions}
        """
    ).strip(),
    "background_sample": dedent(
        """
        プロジェクト「{project_name}」の背景イメージ案を作成してください。
        少なくとも3つのロケーションについて、雰囲気・ライティング・カラーパレットの指針を記載してください。追加指示: {instructions}
        """
    ).strip(),
    "episode_summary": dedent(
        """
        プロジェクト「{project_name}」の第{episode_number}話のあらすじを作成してください。
        ログライン、各幕の構成、次回への引き（クリフハンガー）を Markdown でまとめてください。
        既存の設定: {existing_summary}。追加指示: {instructions}
        """
    ).strip(),
    "episode_script": dedent(
        """
        プロジェクト「{project_name}」第{episode_number}話の脚本抜粋を作成してください。
        台詞とト書きを Markdown 形式で記述し、あらすじ: {existing_summary} を踏まえてください。追加指示: {instructions}
        """
    ).strip(),
    "storyboard_table": dedent(
        """
        プロジェクト「{project_name}」第{episode_number}話の絵コンテ表を作成してください。
        Markdown の表として「タイムコード」「画面」「演出メモ」「補足」を列に含めてください。
        参考となるあらすじ: {existing_summary}。追加要件: {instructions}
        """
    ).strip(),
}


IMAGE_PROMPT_TEMPLATE = dedent(
    """
    プロジェクト「{project_name}」第{episode_number}話のキーフレームとなるコンセプトアートを生成してください。
    シーンの説明: {instructions}
    既存設定との整合性を保ってください: {existing_summary}
    """
).strip()
