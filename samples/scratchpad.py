mint = Spearmint()

@mint.experiment()
def my_exp(a, b, model_config, other_config):
    value = another_fn()
    return a + b + model_config['value'] + other_config['offset'] + value

@mint.bind(ModelConfig, 'path.to.config')
def another_fn(config):
    return config['multiplier'] * 2



def experiment(func: Callable[..., Any]) -> Callable[..., Any]:
    ctx = Context()
    ctx.strategy = Strategy
    ctx.config_resolver = ConfigResolver
    ctx.bindings
    ctx.tracer: Tracer[Span] = Tracer()
    ctx.evaluators = []
    ctx.run(func, args, kwargs)

class Context:
    def __init__(self):
        self.strategy = None
        self.configs = None
        self.bindings = None
        self.tracer = None
        self.span = None

    def run(self, func, args, kwargs):
        with self.tracer.trace(TraceEvent.EXPERIMENT) as span:
            self.span = span
            broadcast(EXPERIMENT_START, self, func=func, args=args, kwargs=kwargs)
            self.strategy(self).run(func, *args, **kwargs)

            broadcast(EXPERIMENT_END, self)


class Strategy:
    def __init__(self, context):
        self.context = context
        self.branches = Branch.generate(self.context)

    @property
    def in_process_branches(self):
        return self.branches[:1]

    @property
    def out_of_process_branches(self):
        return self.branches[1:]
    
    def output(self):
        return self.in_process_branches[0].output

    def run(self, func: Callable[..., Any], *args: Any, **kwargs: Any):
        tasks = []
        for branch in self.out_of_process_branches:
            task = ThreadPoolExecutor().submit(branch.run,*args, **kwargs)
            tasks.append(task)
        for branch in self.in_process_branches:
            branch.run(*args, **kwargs)
        
        return self.output()
    
class Branch:
    def run(self, func, *args, **kwargs):
        with self.context.tracer.trace(TraceEvent.BRANCH, context={"branch_id": self.id}):
            self.output = func(*args, **kwargs)
    
    def evaluate(self):
        for evaluator in self.context.evaluators:
            evaluator.evaluate(self.output, self.context)

class Evaluator:
    def evaluate(self, output, context):
        score = 1.0 if len(output) > 10 else 0.0
        context.tracer.add_event(TraceEvent.EVALUATOR, {"score": score})

@event(EXPERIMENT_START)
def on_trace(ctx, func, args, kwargs):
    for k, v in ctx.kwargs.items():
        ctx.span.add_attribute(f"kwargs.{k}", v)

@event(EXPERIMENT_END)
def on_experiment_end(ctx, span):
    ctx.branch_container


