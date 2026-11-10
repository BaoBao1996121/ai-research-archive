> 历史研究归档 · 2026-11-10 发布 · 程序扫描；未逐篇全文审阅。原有日期、观点、数据和命令保留历史语境，未经本次逐项事实核验或运行复现；请结合[归档说明](../../../ARCHIVE_POLICY.md)阅读。

# ASR/TTS集成方法

## 问题
如何集成豆包和Cocoro语音API以解决专有名词断字问题？

## 判断
集成豆包和Cocoro语音API是解决专有名词断字问题的有效方法。

## 规则
1. **配置文件设置**：
   - 在`.env`文件中添加以下配置：
     ```plaintext
     DOUBAO_ASR_URL=ws://[REDACTED]:8848
     DOUBAO_TTS_URL=http://[REDACTED]:8845
     ```
   - 确保配置文件同步到所有相关服务。

2. **API调用**：
   - 使用`utils/doubao_asr.py`进行语音识别：
     ```python
     from utils.doubao_asr import DoubaoASR
     asr = DoubaoASR()
     transcription = asr.recognize(audio_file)
     ```
   - 使用`utils/doubao_tts.py`进行语音合成：
     ```python
     from utils.doubao_tts import DoubaoTTS
     tts = DoubaoTTS()
     audio = tts.synthesize(text)
     ```

3. **错误处理**：
   - 在API调用时添加异常处理：
     ```python
     try:
         # API调用代码
     except Exception as e:
         print(f"API调用失败: {e}")
         # 处理逻辑
     ```

## 例外
- 如果专有名词处理能力不足，需验证豆包和Cocoro的专有名词处理能力。

## 检查清单
1. 验证配置文件是否正确同步。
2. 检查API调用是否正常。
3. 验证专有名词处理能力是否符合预期。
