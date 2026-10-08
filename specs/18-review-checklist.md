# 人工审查清单

> 用途：Specs baseline 冻结前，学生逐项人工核对；每项必须给出「通过 / 不通过 / 修订意见」。
> 状态：待审查

---

## A. 需求规格（02-requirements.md）

- [ ] A1 是否覆盖实验要求的全部功能（注册、办证、图书维护、检索、借、还、预约、罚款、规则维护）？
- [ ] A2 每条 FR 是否都有**可验证**的验收标准？
- [ ] A3 借阅数量与期限矩阵（5/30、10/60、15/90、20/90）是否符合预期？
- [ ] A4 罚款单价表（0.5/1.0/0.2/0.5/2.0）是否符合预期？
- [ ] A5 权限矩阵是否与课程要求一致（借还必须由管理员代理）？
- [ ] A6 续借参与者（Reader 本人 或 Librarian）是否为最终决定？
- [ ] A7 评论审核（PENDING → APPROVED/REJECTED）是否已正确写入 FR-022/023/024 与 BR-018？
- [ ] A8 预约 7 天有效期是否已写入 BR-008 且"过期不排队、不阻塞续借"？
- [ ] A9 「待确认问题」中 OPEN-01、02、05、06 是否接受默认取值？
- [ ] A10 是否存在与 `00-project-brief.md`「暂不实现」冲突的需求？

## B. 用例文本（03-use-cases.md）

- [ ] B1 用例是否覆盖全部参与者与核心用例？
- [ ] B2 办理借书是否包含：验证借阅证 → 检查数量 → 检查超期 → 检查未缴罚款 → 校验副本 → 创建 Loan？
- [ ] B3 还书是否覆盖两段式流程（BR-020）：读者申请（他人记录 403、重复申请 400、非 BORROWED 400）、馆员审核（通过 / 驳回、无待审核申请 400、非管理员 403）、现场办理（非本馆藏书 400、未找到记录 400、超期生成罚款）？
- [ ] B4 预约是否包含：重复预约、已借同标题、排队位次、有效期分支？
- [ ] B5 续借是否包含：已归还、已逾期、达上限、存在他人预约、已提交归还申请五类异常？
- [ ] B6 每个用例的异常事件流是否都能映射到具体 `code`？
- [ ] B7 用例编号与需求 FR 的关联是否完整？

## C. 用例图（04-use-case-model.puml）

- [ ] C1 参与者是否包含 Reader、StudentReader、TeacherReader、Librarian、SystemAdmin？
- [ ] C2 Student / Teacher 是否泛化自 Reader？
- [ ] C3 include 关系是否正确（借书→验证借阅证、还书→计算罚款）？
- [ ] C4 extend 关系是否合理（图书不可借 → 转为预约）？
- [ ] C5 图与用例文本是否一一对应（含 UC-021 审核评论）？
- [ ] C6 文件能否被 PlantUML 正常渲染？

## D. 领域模型（05-domain-model.md）

- [ ] D1 领域类是否来自业务概念，而非数据库表的机械翻译？
- [ ] D2 是否体现不同读者类型（Student / Teacher 继承 Reader）？
- [ ] D3 是否体现不同借出物类型（Book / Magazine / Thesis 继承 LibraryItem）？
- [ ] D4 借阅规则是否抽象为 `BorrowPolicy`？
- [ ] D5 罚款规则是否抽象为 `FineRule`？
- [ ] D6 `Loan` 是否能表达借出、归还、续借次数与超期？
- [ ] D7 `Reservation` 是否支持排队与有效期？
- [ ] D8 是否明确区分实体、值对象、策略对象与领域服务？
- [ ] D9 跨聚合是否只通过 ID 引用？

## E. 领域类图（06-domain-class-diagram.puml）

- [ ] E1 是否表达类、属性与核心方法？
- [ ] E2 是否表达继承、关联、聚合/组合与多重性？
- [ ] E3 Reader 与子类关系是否清晰？
- [ ] E4 LibraryItem 与子类关系是否清晰？
- [ ] E5 `BorrowPolicy` / `FineRule` 的作用是否在图中可见？
- [ ] E6 是否**没有**混入 Controller、Repository 实现、DTO 等设计类？

## F. 架构设计（07-architecture.md）

- [ ] F1 是否满足分层架构（presentation / application / domain / infrastructure）？
- [ ] F2 是否说明每层职责、模块划分、依赖方向？
- [ ] F3 是否说明权限控制策略（令牌 + 角色 + 数据级）？
- [ ] F4 是否说明异常处理策略与 `code` 映射？
- [ ] F5 是否明确事务边界（借书、还书为同一事务）？
- [ ] F6 业务规则是否全部落在策略/领域对象，而非 Controller？
- [ ] F7 是否说明使用的设计模式（Strategy / Repository / Service Layer / DTO / Factory）？
- [ ] F8 对话式 Agent 三层结构是否与 `.codebuddy` 现有结构一致？

## G. 包图（08-package-diagram.puml）

- [ ] G1 是否表达分层与主要包？
- [ ] G2 依赖方向是否自上而下？
- [ ] G3 Controller 是否**未**直接依赖 Repository？
- [ ] G4 Infrastructure 是否实现 Repository 接口？
- [ ] G5 领域层是否未依赖 FastAPI / SQLAlchemy？

## H. 数据库设计（13-database-design.md）

- [ ] H1 是否覆盖全部需持久化对象（含 accounts、auth_tokens、policies、reviews）？
- [ ] H2 `borrow_cards.card_no` 是否唯一？
- [ ] H3 `library_items.barcode` 是否唯一？
- [ ] H4 `loans` 是否能区分在借、已还、超期，并记录续借次数？
- [ ] H5 `reservations` 是否支持排队与有效期（expires_at）？
- [ ] H6 `fine_rules` 是否支持不同借出物类型？
- [ ] H7 `borrow_policies` 是否支持不同读者类型？
- [ ] H8 外键、唯一约束、默认值、索引是否完整？
- [ ] H9 继承映射策略（单表继承）是否合理？
- [ ] H10 是否明确"删除旧库重建"的初始化策略？

## I. 风险与流程（17 / 19）

- [ ] I1 风险分析是否覆盖需求、建模、架构、数据库、权限、测试、Agent 使用？
- [ ] I2 高风险项（R-06/08/10/12/16/17/21/22）是否有明确缓解措施？
- [ ] I3 是否准备按 `19-ai-usage-log.md` 模板记录每次 Agent 使用？

---

## 审查结论

| 项目 | 结论 |
|---|---|
| 审查人 | |
| 审查日期 | |
| 不通过项与修订意见 | |
| 是否同意冻结 `experiment1-specs-baseline-v1` | 是 / 否 |
