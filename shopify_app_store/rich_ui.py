# -*- coding: utf-8 -*-
"""Rich interactive terminal dashboard for Scrapy spider."""

import time
from collections import deque
from datetime import timedelta

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from scrapy import signals


class RichDashboard:
    """Scrapy Extension that provides a live Rich terminal dashboard."""

    def __init__(self, crawler):
        self.crawler = crawler
        self.console = Console()

        # Counters
        self.total_apps = 0
        self.scraped_apps = 0
        self.skipped_apps = 0
        self.error_count = 0
        self.rate_limit_count = 0
        self.retry_count = 0

        # Item counters
        self.item_counts = {
            'App': 0,
            'KeyBenefit': 0,
            'PricingPlan': 0,
            'PricingPlanFeature': 0,
            'Category': 0,
            'AppCategory': 0,
            'AppReview': 0,
        }

        # Activity log (last 8 entries)
        self.activity_log = deque(maxlen=8)

        # Timing
        self.start_time = None

        # Rich Live display
        self.live = None
        self.progress = None
        self.app_task_id = None

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler)
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        crawler.signals.connect(ext.response_received, signal=signals.response_received)
        return ext

    def spider_opened(self, spider):
        self.start_time = time.time()
        spider._rich_ui = self
        self.live = Live(self._build_layout(), console=self.console, refresh_per_second=2)
        self.live.start()

    def spider_closed(self, spider, reason):
        if self.live:
            self.live.stop()

        # Print final summary
        elapsed = time.time() - self.start_time
        self.console.print()
        self.console.print(Panel(
            self._build_summary(elapsed, reason),
            title="[bold cyan]🛍️  Scraping Complete[/]",
            border_style="cyan",
        ))

    def item_scraped(self, item, response, spider):
        class_name = type(item).__name__
        if class_name in self.item_counts:
            self.item_counts[class_name] += 1
        self._refresh()

    def spider_error(self, failure, response, spider):
        self.error_count += 1
        app_name = response.url.split('/')[-1] if response else 'unknown'
        error_msg = str(failure.value)[:60] if failure else 'Unknown error'
        self.activity_log.append(('error', app_name, error_msg))
        self._refresh()

    def response_received(self, response, request, spider):
        if response.status == 429:
            self.rate_limit_count += 1
            app_name = request.url.split('/')[-1]
            self.activity_log.append(('rate_limit', app_name, '429 Rate Limited'))
            self._refresh()

    def notify_scraped(self, app_url):
        """Called by spider when an app page is successfully parsed."""
        self.scraped_apps += 1
        app_name = app_url.rstrip('/').split('/')[-1]
        item_count = sum(self.item_counts.values())
        self.activity_log.append(('success', app_name, f'{self.item_counts["App"]} apps total'))
        self._refresh()

    def notify_skipped(self):
        """Called by spider when an app is skipped (unchanged since last scrape)."""
        self.skipped_apps += 1
        self._refresh()

    def set_total_apps(self, count):
        """Called by spider after parsing sitemap to set total app count."""
        self.total_apps = count
        self._refresh()

    def _refresh(self):
        if self.live:
            self.live.update(self._build_layout())

    def _build_layout(self):
        """Build the full dashboard layout."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        elapsed_str = str(timedelta(seconds=int(elapsed)))

        # Speed calculation
        speed = (self.scraped_apps / elapsed * 60) if elapsed > 0 else 0

        # === Header ===
        header = Text("🛍️  Shopify App Store Scraper", style="bold cyan")

        # === Progress Section ===
        progress_table = Table.grid(padding=(0, 1))
        progress_table.add_column(ratio=1)

        # App progress bar
        if self.total_apps > 0:
            pct = (self.scraped_apps + self.skipped_apps) / self.total_apps * 100
            filled = int(pct / 100 * 30)
            bar = f"[green]{'█' * filled}[/][dim]{'░' * (30 - filled)}[/]"
            progress_text = f"  Apps    {bar}  [bold]{self.scraped_apps + self.skipped_apps:,}[/] / [bold]{self.total_apps:,}[/]  [dim]({pct:.1f}%)[/]"
        else:
            progress_text = "  Apps    [dim]Waiting for sitemap...[/]"

        progress_table.add_row(progress_text)

        # === Stats Row ===
        stats = Table.grid(padding=(0, 2))
        stats.add_column()
        stats.add_column()
        stats.add_column()
        stats.add_column()
        stats.add_row(
            f"  ⏱ Elapsed: [bold]{elapsed_str}[/]",
            f"📊 Speed: [bold cyan]{speed:.0f}[/] apps/min",
            f"⏭ Skipped: [bold yellow]{self.skipped_apps:,}[/]",
            f"🔄 Retries: [bold]{self.retry_count}[/]",
        )
        stats.add_row(
            f"  ✅ Scraped: [bold green]{self.scraped_apps:,}[/]",
            f"📦 Items: [bold cyan]{sum(self.item_counts.values()):,}[/]",
            f"⚠️  Errors: [bold red]{self.error_count}[/]",
            f"🚫 429s: [bold red]{self.rate_limit_count}[/]",
        )

        # === Item Counts Table ===
        items_table = Table(
            title="📊 Item Counts",
            show_header=True,
            header_style="bold",
            expand=True,
            title_style="bold white",
            padding=(0, 1),
        )
        items_table.add_column("Type", style="cyan", ratio=2)
        items_table.add_column("Count", justify="right", style="bold green", ratio=1)

        for item_type, count in self.item_counts.items():
            emoji = {
                'App': '📱', 'KeyBenefit': '✨', 'PricingPlan': '💰',
                'PricingPlanFeature': '📋', 'Category': '🏷️',
                'AppCategory': '🔗', 'AppReview': '⭐',
            }.get(item_type, '•')
            items_table.add_row(f"{emoji} {item_type}", f"{count:,}")

        # === Activity Log ===
        activity_lines = []
        for entry_type, name, detail in self.activity_log:
            if entry_type == 'success':
                activity_lines.append(f"  [green]✓[/] {name:<35} [dim]{detail}[/]")
            elif entry_type == 'error':
                activity_lines.append(f"  [red]✗[/] {name:<35} [red]{detail}[/]")
            elif entry_type == 'rate_limit':
                activity_lines.append(f"  [yellow]⚠[/] {name:<35} [yellow]{detail}[/]")
            elif entry_type == 'skip':
                activity_lines.append(f"  [dim]⏭[/] {name:<35} [dim]{detail}[/]")

        if not activity_lines:
            activity_lines.append("  [dim]Waiting for first response...[/]")

        activity_text = "\n".join(activity_lines)

        # === Compose Layout ===
        layout_parts = Table.grid(padding=(0, 0))
        layout_parts.add_column(ratio=1)

        layout_parts.add_row("")
        layout_parts.add_row(progress_text)
        layout_parts.add_row("")
        layout_parts.add_row(stats)
        layout_parts.add_row("")

        # Side-by-side: items + activity
        side_by_side = Table.grid(padding=(0, 1))
        side_by_side.add_column(ratio=2)
        side_by_side.add_column(ratio=3)
        side_by_side.add_row(
            items_table,
            Panel(activity_text, title="[bold]📝 Recent Activity[/]", border_style="dim"),
        )
        layout_parts.add_row(side_by_side)

        return Panel(
            layout_parts,
            title=f"[bold cyan]{header}[/]",
            border_style="cyan",
            padding=(0, 1),
        )

    def _build_summary(self, elapsed, reason):
        """Build the final summary panel content."""
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        speed = (self.scraped_apps / elapsed * 60) if elapsed > 0 else 0

        summary = Table.grid(padding=(0, 2))
        summary.add_column()
        summary.add_column()

        summary.add_row(f"  Reason: [bold]{reason}[/]", f"Duration: [bold]{elapsed_str}[/]")
        summary.add_row(
            f"  Scraped: [bold green]{self.scraped_apps:,}[/] apps",
            f"Skipped: [bold yellow]{self.skipped_apps:,}[/] apps",
        )
        summary.add_row(
            f"  Total Items: [bold cyan]{sum(self.item_counts.values()):,}[/]",
            f"Speed: [bold]{speed:.0f}[/] apps/min",
        )
        summary.add_row(
            f"  Errors: [bold red]{self.error_count}[/]",
            f"Rate Limits: [bold red]{self.rate_limit_count}[/]",
        )

        items_detail = " | ".join(
            f"{k}: [bold]{v:,}[/]" for k, v in self.item_counts.items() if v > 0
        )
        if items_detail:
            summary.add_row("", "")
            summary.add_row(f"  [dim]{items_detail}[/]", "")

        return summary
