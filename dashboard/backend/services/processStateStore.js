"use strict";
/**
 * Process State Store - Persistent State Management
 *
 * Handles:
 * - Storing process information to disk
 * - Loading state across application restarts
 * - Tracking processes across sessions
 * - Clean state cleanup
 * - Data integrity and error handling
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
exports.ProcessStateStore = void 0;
var fs = __importStar(require("fs/promises"));
var path = __importStar(require("path"));
var ProcessStateStore = /** @class */ (function () {
    function ProcessStateStore(dbPath) {
        if (dbPath === void 0) { dbPath = path.join(process.cwd(), 'process-state.json'); }
        this.state = new Map();
        this.dbPath = dbPath;
    }
    /**
     * Load state from disk
     */
    ProcessStateStore.prototype.load = function () {
        return __awaiter(this, void 0, void 0, function () {
            var data, parsed, _i, _a, _b, id, info, processInfo, error_1;
            return __generator(this, function (_c) {
                switch (_c.label) {
                    case 0:
                        _c.trys.push([0, 2, , 3]);
                        return [4 /*yield*/, fs.readFile(this.dbPath, 'utf-8')];
                    case 1:
                        data = _c.sent();
                        parsed = JSON.parse(data);
                        this.state.clear();
                        for (_i = 0, _a = Object.entries(parsed); _i < _a.length; _i++) {
                            _b = _a[_i], id = _b[0], info = _b[1];
                            processInfo = info;
                            // Convert string dates back to Date objects
                            if (typeof processInfo.startTime === 'string') {
                                processInfo.startTime = new Date(processInfo.startTime);
                            }
                            this.state.set(id, processInfo);
                        }
                        return [3 /*break*/, 3];
                    case 2:
                        error_1 = _c.sent();
                        // If file doesn't exist or is corrupted, start with empty state
                        if (error_1.code === 'ENOENT') {
                            this.state.clear();
                        }
                        else {
                            console.warn('Error loading process state:', error_1.message);
                            this.state.clear();
                        }
                        return [3 /*break*/, 3];
                    case 3: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Save process to state
     */
    ProcessStateStore.prototype.saveProcess = function (processInfo) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        this.state.set(processInfo.id, processInfo);
                        return [4 /*yield*/, this.persist()];
                    case 1:
                        _a.sent();
                        return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Get process from state
     */
    ProcessStateStore.prototype.getProcess = function (id) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                return [2 /*return*/, this.state.get(id)];
            });
        });
    };
    /**
     * Remove process from state
     */
    ProcessStateStore.prototype.removeProcess = function (id) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        this.state.delete(id);
                        return [4 /*yield*/, this.persist()];
                    case 1:
                        _a.sent();
                        return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Get all processes from state
     */
    ProcessStateStore.prototype.getAllProcesses = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                return [2 /*return*/, Array.from(this.state.values())];
            });
        });
    };
    /**
     * Clear all state
     */
    ProcessStateStore.prototype.clear = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        this.state.clear();
                        return [4 /*yield*/, this.persist()];
                    case 1:
                        _a.sent();
                        return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Persist current state to disk
     */
    ProcessStateStore.prototype.persist = function () {
        return __awaiter(this, void 0, void 0, function () {
            var obj, _i, _a, _b, id, info, data, dir, error_2;
            return __generator(this, function (_c) {
                switch (_c.label) {
                    case 0:
                        _c.trys.push([0, 3, , 4]);
                        obj = {};
                        for (_i = 0, _a = this.state.entries(); _i < _a.length; _i++) {
                            _b = _a[_i], id = _b[0], info = _b[1];
                            obj[id] = info;
                        }
                        data = JSON.stringify(obj, null, 2);
                        dir = path.dirname(this.dbPath);
                        return [4 /*yield*/, fs.mkdir(dir, { recursive: true })];
                    case 1:
                        _c.sent();
                        // Write to file
                        return [4 /*yield*/, fs.writeFile(this.dbPath, data, 'utf-8')];
                    case 2:
                        // Write to file
                        _c.sent();
                        return [3 /*break*/, 4];
                    case 3:
                        error_2 = _c.sent();
                        console.error('Error persisting process state:', error_2.message);
                        throw error_2;
                    case 4: return [2 /*return*/];
                }
            });
        });
    };
    /**
     * Check if a process exists in state
     */
    ProcessStateStore.prototype.hasProcess = function (id) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                return [2 /*return*/, this.state.has(id)];
            });
        });
    };
    return ProcessStateStore;
}());
exports.ProcessStateStore = ProcessStateStore;
