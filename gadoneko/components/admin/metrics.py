from enum import Enum

from hikari import Embed
from lightbulb.ext.neon import ComponentMenu, select_menu, option

from shared.documents import AuditLog


class MetricsOptions(str, Enum):
    COUNT = 'reg-count'
    FAILURE_RATE = 'fail-rate'


pipeline_fails = [
    {
        "$group": {
            "_id": "$exec_cmd.name",
            "countOk": {"$sum": {"$toInt": {"$toBool": "$completed"}}},
            "countOverall": {"$sum": 1}
        }
    },
    {
        "$project": {
            "countOk": True,
            "countFail": {"$subtract": ["$countOverall", "$countOk"]},
            "countOverall": True,
        }
    },
    {
        "$project": {
            "count": {
                "ok": "$countOk",
                "fail": "$countFail",
                "all": "$countOverall",
            },
            "ratio": {
                "failToOk": {"$divide": ["$countFail", "$countOk"]},
                "OkToFail": {"$divide": ["$countOk", "$countFail"]}
            },
            "part": {
                "fail": {"$divide": ["$countFail", "$countOverall"]},
                "ok": {"$divide": ["$countOverall", "$countFail"]}
            }
        }
    }
]


class MetricsMenu(ComponentMenu):
    @option("Fail rate", MetricsOptions.FAILURE_RATE, emoji='😖')
    @select_menu("metrics_menul", "Choose metric")
    async def metrics(self, values: list):
        value = MetricsOptions(values[0])

        match value:
            case MetricsOptions.FAILURE_RATE:
                result = AuditLog.objects().aggregate(pipeline_fails)

                embed = Embed(title="Failure rates", description='Fail ratio should be lower than 0.01')

                for row in result:
                    embed.add_field(
                        row['_id'], row['ratio']['failToOk']
                    )

                await self.edit_msg(embed=embed, content=None)
