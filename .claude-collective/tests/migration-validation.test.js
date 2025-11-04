/**
 * Migration Validation Test Suite
 * Verifies that planner project collective structure matches source project
 */

const fs = require('fs');
const path = require('path');

describe('Collective Structure Migration Validation', () => {
  const sourceRoot = '/home/adamsl/codex_claude_communication';
  const targetRoot = '/home/adamsl/planner';

  describe('Core Configuration Files', () => {
    test('CLAUDE.md files should be identical', () => {
      const sourceFile = fs.readFileSync(path.join(sourceRoot, 'CLAUDE.md'), 'utf8');
      const targetFile = fs.readFileSync(path.join(targetRoot, 'CLAUDE.md'), 'utf8');
      expect(targetFile).toBe(sourceFile);
    });

    test('.claude-collective/CLAUDE.md files should be identical', () => {
      const sourceFile = fs.readFileSync(path.join(sourceRoot, '.claude-collective/CLAUDE.md'), 'utf8');
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/CLAUDE.md'), 'utf8');
      expect(targetFile).toBe(sourceFile);
    });

    test('.claude-collective/DECISION.md files should be identical', () => {
      const sourceFile = fs.readFileSync(path.join(sourceRoot, '.claude-collective/DECISION.md'), 'utf8');
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/DECISION.md'), 'utf8');
      expect(targetFile).toBe(sourceFile);
    });
  });

  describe('Agent Catalog', () => {
    test('.claude-collective/agents.md files should be identical', () => {
      const sourceFile = fs.readFileSync(path.join(sourceRoot, '.claude-collective/agents.md'), 'utf8');
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/agents.md'), 'utf8');
      expect(targetFile).toBe(sourceFile);
    });

    test('agents.md should include @convert-llm-claude-to-codex agent', () => {
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/agents.md'), 'utf8');
      expect(targetFile).toContain('@convert-llm-claude-to-codex');
      expect(targetFile).toContain('MIGRATION SPECIALISTS');
      expect(targetFile).toContain('Automated Claude-to-Codex LLM migration with TDD validation and rollback');
    });
  });

  describe('Routing System', () => {
    test('.claude/commands/van.md files should be identical', () => {
      const sourceFile = fs.readFileSync(path.join(sourceRoot, '.claude/commands/van.md'), 'utf8');
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude/commands/van.md'), 'utf8');
      expect(targetFile).toBe(sourceFile);
    });

    test('van.md should include migration agent routing', () => {
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude/commands/van.md'), 'utf8');
      expect(targetFile).toContain('migrate/convert agent to codex');
      expect(targetFile).toContain('@convert-llm-claude-to-codex');
      expect(targetFile).toContain('Automated LLM migration');
    });
  });

  describe('Framework Files', () => {
    test('.claude-collective/hooks.md files should be identical', () => {
      const sourceFile = fs.readFileSync(path.join(sourceRoot, '.claude-collective/hooks.md'), 'utf8');
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/hooks.md'), 'utf8');
      expect(targetFile).toBe(sourceFile);
    });

    test('.claude-collective/quality.md files should be identical', () => {
      const sourceFile = fs.readFileSync(path.join(sourceRoot, '.claude-collective/quality.md'), 'utf8');
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/quality.md'), 'utf8');
      expect(targetFile).toBe(sourceFile);
    });

    test('.claude-collective/research.md files should be identical', () => {
      const sourceFile = fs.readFileSync(path.join(sourceRoot, '.claude-collective/research.md'), 'utf8');
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/research.md'), 'utf8');
      expect(targetFile).toBe(sourceFile);
    });
  });

  describe('Agent Definition Files', () => {
    test('convert-llm-claude-to-codex.md agent file should exist', () => {
      const targetFile = path.join(targetRoot, '.claude/agents/convert-llm-claude-to-codex.md');
      expect(fs.existsSync(targetFile)).toBe(true);
    });

    test('convert-llm-claude-to-codex.md agent files should be identical', () => {
      const sourceFile = fs.readFileSync(
        path.join(sourceRoot, '.claude/agents/convert-llm-claude-to-codex.md'),
        'utf8'
      );
      const targetFile = fs.readFileSync(
        path.join(targetRoot, '.claude/agents/convert-llm-claude-to-codex.md'),
        'utf8'
      );
      expect(targetFile).toBe(sourceFile);
    });
  });

  describe('Directory Structure', () => {
    test('.claude-collective directory should exist', () => {
      expect(fs.existsSync(path.join(targetRoot, '.claude-collective'))).toBe(true);
    });

    test('.claude/agents directory should exist', () => {
      expect(fs.existsSync(path.join(targetRoot, '.claude/agents'))).toBe(true);
    });

    test('.claude/commands directory should exist', () => {
      expect(fs.existsSync(path.join(targetRoot, '.claude/commands'))).toBe(true);
    });

    test('.claude-collective/tests directory should exist', () => {
      expect(fs.existsSync(path.join(targetRoot, '.claude-collective/tests'))).toBe(true);
    });
  });

  describe('Auto-Delegation Infrastructure', () => {
    test('DECISION.md should contain auto-delegation logic', () => {
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/DECISION.md'), 'utf8');
      expect(targetFile).toContain('AUTO-DELEGATION INFRASTRUCTURE');
      expect(targetFile).toContain('DUAL AUTO-DELEGATION SYSTEM');
      expect(targetFile).toContain('MY HANDOFF MESSAGES');
      expect(targetFile).toContain('AGENT HANDOFF MESSAGES');
    });

    test('DECISION.md should contain routing decisions', () => {
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/DECISION.md'), 'utf8');
      expect(targetFile).toContain('ROUTING DECISIONS');
      expect(targetFile).toContain('/van commands');
      expect(targetFile).toContain('normal questions');
      expect(targetFile).toContain('agent handoffs');
    });
  });

  describe('Behavioral Operating System', () => {
    test('CLAUDE.md should contain collective behavioral rules header', () => {
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/CLAUDE.md'), 'utf8');
      expect(targetFile).toContain('COLLECTIVE BEHAVIORAL RULES');
      expect(targetFile).toContain('ONLY ACTIVE WHEN /VAN CALLED');
    });

    test('CLAUDE.md should import all framework files', () => {
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/CLAUDE.md'), 'utf8');
      expect(targetFile).toContain('@./.claude/commands/van.md');
      expect(targetFile).toContain('@./.claude-collective/agents.md');
      expect(targetFile).toContain('@./.claude-collective/hooks.md');
      expect(targetFile).toContain('@./.claude-collective/quality.md');
      expect(targetFile).toContain('@./.claude-collective/research.md');
    });

    test('CLAUDE.md should contain prime directives', () => {
      const targetFile = fs.readFileSync(path.join(targetRoot, '.claude-collective/CLAUDE.md'), 'utf8');
      expect(targetFile).toContain('Prime Directives for Sub-Agent Collective');
      expect(targetFile).toContain('DIRECTIVE 1: NEVER IMPLEMENT DIRECTLY');
      expect(targetFile).toContain('DIRECTIVE 2: COLLECTIVE ROUTING PROTOCOL');
      expect(targetFile).toContain('DIRECTIVE 3: TEST-DRIVEN VALIDATION');
    });
  });
});

describe('Migration Completeness', () => {
  test('Backup file should exist', () => {
    const backupPattern = /planner_backup_\d{8}_\d{6}\.tar\.gz/;
    const parentDir = '/home/adamsl';
    const files = fs.readdirSync(parentDir);
    const backupExists = files.some(file => backupPattern.test(file));
    expect(backupExists).toBe(true);
  });

  test('All critical collective files should exist in target', () => {
    const targetRoot = '/home/adamsl/planner';
    const criticalFiles = [
      'CLAUDE.md',
      '.claude-collective/CLAUDE.md',
      '.claude-collective/DECISION.md',
      '.claude-collective/agents.md',
      '.claude-collective/hooks.md',
      '.claude-collective/quality.md',
      '.claude-collective/research.md',
      '.claude/commands/van.md',
      '.claude/agents/convert-llm-claude-to-codex.md'
    ];

    criticalFiles.forEach(file => {
      expect(fs.existsSync(path.join(targetRoot, file))).toBe(true);
    });
  });
});
