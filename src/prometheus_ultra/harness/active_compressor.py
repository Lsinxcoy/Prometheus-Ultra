"""ActiveCompressor — Active Context Compression (arXiv 2601.07190).

Model 自主决定何时压缩的锯齿模式。
Token 使用超过阈值时触发压缩，不是固定阈值。
"""

from __future__ import annotations

import logging
import math
import re
import time

logger = logging.getLogger(__name__)

_DEFAULT_MAX_TOKENS = 25000
_DEFAULT_COMPRESSION_RATIO = 0.3
_DEFAULT_SAW_TOOTH_THRESHOLD = 0.85


class ActiveCompressor:
    """主动上下文压缩器。"""

    def __init__(self, max_tokens: int = _DEFAULT_MAX_TOKENS,
                 compression_ratio: float = _DEFAULT_COMPRESSION_RATIO,
                 saw_tooth_threshold: float = _DEFAULT_SAW_TOOTH_THRESHOLD):
        self._max_tokens = max_tokens
        self._compression_ratio = compression_ratio
        self._saw_tooth_threshold = saw_tooth_threshold
        self._compress_count = 0
        self._total_tokens_before = 0
        self._total_tokens_after = 0

    def estimate_tokens(self, text: str) -> int:
        """估算文本 token 数（近似：英文词数×1.3 + 中文字符数）。"""
        if not text:
            return 0
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        return int(english_words * 1.3 + chinese_chars)

    def should_compress(self, context: list[str]) -> bool:
        """判断是否需要压缩。"""
        total = sum(self.estimate_tokens(c) for c in context)
        if total == 0:
            return False
        usage_ratio = total / self._max_tokens
        return usage_ratio >= self._saw_tooth_threshold

    def compress(self, context: list[str], task_type: str = "general") -> list[str]:
        """压缩上下文。返回压缩后的 tokens。"""
        if not context:
            return []
        
        total_before = sum(self.estimate_tokens(c) for c in context)
        self._total_tokens_before += total_before

        # 锯齿模式：压缩 30% 的内容
        n_compress = max(1, int(len(context) * self._compression_ratio))
        
        # 优先压缩较老的内容（前 1/3）
        compress_candidates = context[:len(context) // 3]
        if not compress_candidates:
            compress_candidates = context[:n_compress]

        compressed_parts = []
        for i, part in enumerate(compress_candidates[:n_compress]):
            compressed = self._compress_part(part, task_type)
            compressed_parts.append(compressed)
            context[context.index(part)] = compressed

        self._compress_count += len(compressed_parts)
        total_after = sum(self.estimate_tokens(c) for c in context)
        self._total_tokens_after += total_after

        logger.debug("Compressed %d/%d parts: %d→%d tokens (%.1f%%)",
                     len(compressed_parts), len(context),
                     total_before, total_after,
                     (1 - total_after / max(total_before, 1)) * 100)

        return context

    def _compress_part(self, text: str, task_type: str) -> str:
        """压缩一段文本。"""
        if len(text) < 50:
            return text
        lines = text.split('\n')
        if len(lines) > 3:
            return lines[0] + '\n... (' + str(len(lines) - 2) + ' lines omitted)\n' + lines[-1]
        words = text.split()
        if len(words) > 30:
            return ' '.join(words[:15]) + '...' + ' '.join(words[-5:])
        return text

    def estimate_savings(self, context: list[str]) -> float:
        total = sum(self.estimate_tokens(c) for c in context)
        if total == 0:
            return 0.0
        n = max(1, int(len(context) * self._compression_ratio))
        avg_len = total / len(context)
        return (n * avg_len * 0.3) / total  # approximate 30% of candidate parts

    def get_stats(self) -> dict:
        return {
            "compress_count": self._compress_count,
            "tokens_before": self._total_tokens_before,
            "tokens_after": self._total_tokens_after,
            "savings_pct": round(
                (1 - self._total_tokens_after / max(self._total_tokens_before, 1)) * 100, 1
            ) if self._total_tokens_before > 0 else 0,
        }
