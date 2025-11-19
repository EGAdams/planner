"use strict";
/**
 * Agent Discovery Service
 * Responsibility: Scan directories for agent.json files and register them as managed agents.
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AgentDiscoveryService = void 0;
var fs = __importStar(require("fs/promises"));
var path = __importStar(require("path"));
var AgentDiscoveryService = /** @class */ (function () {
    function AgentDiscoveryService() {
        this.discoveredAgents = new Map();
    }
    /**
     * Discover agents in the given root directories
     */
    AgentDiscoveryService.prototype.discover = function (rootPaths) {
        return __awaiter(this, void 0, void 0, function () {
            var _i, rootPaths_1, rootPath, absolutePath, error_1;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        this.discoveredAgents.clear();
                        _i = 0, rootPaths_1 = rootPaths;
                        _a.label = 1;
                    case 1:
                        if (!(_i < rootPaths_1.length)) return [3 /*break*/, 6];
                        rootPath = rootPaths_1[_i];
                        _a.label = 2;
                    case 2:
                        _a.trys.push([2, 4, , 5]);
                        absolutePath = path.resolve(rootPath);
                        return [4 /*yield*/, this.scanDirectory(absolutePath)];
                    case 3:
                        _a.sent();
                        return [3 /*break*/, 5];
                    case 4:
                        error_1 = _a.sent();
                        console.error("Failed to scan directory ".concat(rootPath, ":"), error_1);
                        return [3 /*break*/, 5];
                    case 5:
                        _i++;
                        return [3 /*break*/, 1];
                    case 6: return [2 /*return*/, Object.fromEntries(this.discoveredAgents)];
                }
            });
        });
    };
    /**
     * Recursively scan directory for agent.json
     */
    AgentDiscoveryService.prototype.scanDirectory = function (dir_1) {
        return __awaiter(this, arguments, void 0, function (dir, depth) {
            var entries, _i, entries_1, entry, fullPath, error_2;
            if (depth === void 0) { depth = 0; }
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        // Limit recursion depth to avoid performance issues or infinite loops
                        if (depth > 5)
                            return [2 /*return*/];
                        _a.label = 1;
                    case 1:
                        _a.trys.push([1, 9, , 10]);
                        return [4 /*yield*/, fs.readdir(dir, { withFileTypes: true })];
                    case 2:
                        entries = _a.sent();
                        _i = 0, entries_1 = entries;
                        _a.label = 3;
                    case 3:
                        if (!(_i < entries_1.length)) return [3 /*break*/, 8];
                        entry = entries_1[_i];
                        fullPath = path.join(dir, entry.name);
                        if (!entry.isDirectory()) return [3 /*break*/, 5];
                        // Skip node_modules, .git, etc.
                        if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === 'dist') {
                            return [3 /*break*/, 7];
                        }
                        return [4 /*yield*/, this.scanDirectory(fullPath, depth + 1)];
                    case 4:
                        _a.sent();
                        return [3 /*break*/, 7];
                    case 5:
                        if (!(entry.name === 'agent.json')) return [3 /*break*/, 7];
                        return [4 /*yield*/, this.processAgentConfig(dir, fullPath)];
                    case 6:
                        _a.sent();
                        _a.label = 7;
                    case 7:
                        _i++;
                        return [3 /*break*/, 3];
                    case 8: return [3 /*break*/, 10];
                    case 9:
                        error_2 = _a.sent();
                        return [3 /*break*/, 10];
                    case 10: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Process an agent.json file and create a ServerConfig
     */
    AgentDiscoveryService.prototype.processAgentConfig = function (dir, configPath) {
        return __awaiter(this, void 0, void 0, function () {
            var content, metadata, id, command, config, error_3;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        _a.trys.push([0, 3, , 4]);
                        return [4 /*yield*/, fs.readFile(configPath, 'utf-8')];
                    case 1:
                        content = _a.sent();
                        metadata = JSON.parse(content);
                        id = metadata.name ? metadata.name.toLowerCase().replace(/\s+/g, '-') : path.basename(dir);
                        return [4 /*yield*/, this.inferCommand(dir)];
                    case 2:
                        command = _a.sent();
                        if (command) {
                            config = {
                                name: metadata.name || id,
                                command: command,
                                cwd: dir,
                                color: this.generateColor(id),
                                ports: [], // Agents might not have ports, or we'd need to parse them from somewhere else
                                type: 'agent'
                            };
                            this.discoveredAgents.set(id, config);
                            console.log("Discovered agent: ".concat(id, " in ").concat(dir));
                        }
                        else {
                            console.warn("Could not infer run command for agent in ".concat(dir));
                        }
                        return [3 /*break*/, 4];
                    case 3:
                        error_3 = _a.sent();
                        console.error("Failed to process agent config at ".concat(configPath, ":"), error_3);
                        return [3 /*break*/, 4];
                    case 4: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Infer the run command for an agent based on file structure
     */
    AgentDiscoveryService.prototype.inferCommand = function (dir) {
        return __awaiter(this, void 0, void 0, function () {
            var files, venvPath, hasVenv, pkgContent, pkg, error_4;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        _a.trys.push([0, 6, , 7]);
                        return [4 /*yield*/, fs.readdir(dir)];
                    case 1:
                        files = _a.sent();
                        if (!files.includes('main.py')) return [3 /*break*/, 3];
                        venvPath = path.join(dir, '.venv');
                        return [4 /*yield*/, this.fileExists(venvPath)];
                    case 2:
                        hasVenv = _a.sent();
                        if (hasVenv) {
                            return [2 /*return*/, "".concat(path.join(dir, '.venv/bin/python'), " main.py")];
                        }
                        else {
                            // Fallback to system python or a shared venv if we knew where it was
                            // For now, assume 'python3' is available or use the workspace venv
                            return [2 /*return*/, "/home/adamsl/planner/.venv/bin/python main.py"];
                        }
                        _a.label = 3;
                    case 3:
                        if (!files.includes('package.json')) return [3 /*break*/, 5];
                        return [4 /*yield*/, fs.readFile(path.join(dir, 'package.json'), 'utf-8')];
                    case 4:
                        pkgContent = _a.sent();
                        pkg = JSON.parse(pkgContent);
                        if (pkg.scripts && pkg.scripts.start) {
                            return [2 /*return*/, "npm start"];
                        }
                        if (files.includes('index.js')) {
                            return [2 /*return*/, "node index.js"];
                        }
                        if (files.includes('main.js')) {
                            return [2 /*return*/, "node main.js"];
                        }
                        if (files.includes('dist/index.js')) {
                            return [2 /*return*/, "node dist/index.js"];
                        }
                        _a.label = 5;
                    case 5: return [2 /*return*/, null];
                    case 6:
                        error_4 = _a.sent();
                        return [2 /*return*/, null];
                    case 7: return [2 /*return*/];
                }
            });
        });
    };
    AgentDiscoveryService.prototype.fileExists = function (path) {
        return __awaiter(this, void 0, void 0, function () {
            var _a;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        _b.trys.push([0, 2, , 3]);
                        return [4 /*yield*/, fs.access(path)];
                    case 1:
                        _b.sent();
                        return [2 /*return*/, true];
                    case 2:
                        _a = _b.sent();
                        return [2 /*return*/, false];
                    case 3: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Generate a consistent pastel color from a string
     */
    AgentDiscoveryService.prototype.generateColor = function (str) {
        var hash = 0;
        for (var i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }
        // Generate pastel color
        var h = Math.abs(hash) % 360;
        return "hsl(".concat(h, ", 70%, 90%)");
    };
    return AgentDiscoveryService;
}());
exports.AgentDiscoveryService = AgentDiscoveryService;
